import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# Import custom modules
from database import DatabaseManager
from document_parser import DocumentParser
from file_storage import FileStorageManager
from nlp_processor import NLPProcessor
from matching_engine import MatchingEngine
from utils import validate_email, validate_phone

# Initialize components
@st.cache_resource
def init_components():
    """Initialize all application components"""
    db_manager = DatabaseManager()
    document_parser = DocumentParser()
    file_storage = FileStorageManager()
    nlp_processor = NLPProcessor()
    matching_engine = MatchingEngine()
    return db_manager, document_parser, file_storage, nlp_processor, matching_engine

# Page configuration
st.set_page_config(
    page_title="Resume Shortlisting System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
db_manager, document_parser, file_storage, nlp_processor, matching_engine = init_components()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page",
    ["Candidate Registration", "Admin Panel", "View Candidates", "Job Requirements"]
)

# Main application logic
if page == "Candidate Registration":
    st.title("📄 Candidate Registration")
    st.write("Please fill in your details and upload your resume")
    
    with st.form("candidate_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name *", placeholder="Enter your full name")
            email = st.text_input("Email *", placeholder="your.email@example.com")
            phone = st.text_input("Phone Number *", placeholder="+1-234-567-8900")
            
        with col2:
            location = st.text_input("Location", placeholder="City, State/Country")
            experience_years = st.number_input("Years of Experience", min_value=0, max_value=50, value=0)
            
        st.subheader("Resume Upload")
        uploaded_file = st.file_uploader(
            "Upload your resume",
            type=['pdf', 'doc', 'docx', 'txt'],
            help="Supported formats: PDF, DOC, DOCX, TXT"
        )
        
        submitted = st.form_submit_button("Submit Application")
        
        if submitted:
            # Validation
            errors = []
            if not full_name.strip():
                errors.append("Full name is required")
            if not email.strip():
                errors.append("Email is required")
            elif not validate_email(email):
                errors.append("Please enter a valid email address")
            if not phone.strip():
                errors.append("Phone number is required")
            elif not validate_phone(phone):
                errors.append("Please enter a valid phone number")
            if uploaded_file is None:
                errors.append("Resume upload is required")
                
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Check if email already exists
                if db_manager.email_exists(email):
                    st.error("An application with this email already exists!")
                else:
                    try:
                        # Process document
                        with st.spinner("Processing your resume..."):
                            file_content = uploaded_file.read()
                            filename = uploaded_file.name
                            
                            # Validate document
                            validation = document_parser.validate_document(file_content, filename)
                            if not validation['is_valid']:
                                st.error(f"Invalid document: {'; '.join(validation['messages'])}")
                            else:
                                # Extract text from document
                                resume_text = document_parser.extract_text_from_file(file_content, filename)
                                
                                if not resume_text.strip():
                                    st.error("Could not extract text from the document. Please ensure it contains readable text.")
                                else:
                                    # Store file in storage system
                                    file_info = file_storage.store_resume_file(
                                        file_content, filename, 0  # Temporary candidate_id
                                    )
                                    
                                    # Process with NLP
                                    education_data, skills_data = nlp_processor.extract_entities(resume_text)
                                    
                                    # Store in database
                                    candidate_id = db_manager.add_candidate(
                                        full_name=full_name,
                                        email=email,
                                        phone=phone,
                                        location=location,
                                        experience_years=experience_years,
                                        resume_text=resume_text,
                                        education_data=education_data,
                                        skills_data=skills_data,
                                        file_info=file_info
                                    )
                                    
                                    # Update file with actual candidate_id
                                    file_info['candidate_id'] = candidate_id
                                
                                st.success(f"✅ Application submitted successfully! Candidate ID: {candidate_id}")
                                st.info("Your application is now pending review. You will be contacted if shortlisted.")
                                
                                # Show extracted information
                                with st.expander("View Extracted Information"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.subheader("Education")
                                        if education_data:
                                            for edu in education_data:
                                                st.write(f"• {edu.get('degree', 'N/A')} - {edu.get('institution', 'N/A')}")
                                        else:
                                            st.write("No education information detected")
                                    
                                    with col2:
                                        st.subheader("Skills")
                                        if skills_data:
                                            for skill in skills_data:
                                                st.write(f"• {skill.get('skill', 'N/A')}")
                                        else:
                                            st.write("No skills detected")
                                
                    except Exception as e:
                        st.error(f"Error processing application: {str(e)}")

elif page == "Admin Panel":
    st.title("🔧 Admin Control Panel")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Matching & Shortlisting", "Candidate Management", "Export Data", "File Storage"])
    
    with tab1:
        st.subheader("Automatic Candidate Matching")
        
        # Threshold configuration
        col1, col2 = st.columns([2, 1])
        with col1:
            current_threshold = matching_engine.get_threshold()
            new_threshold = st.slider(
                "Matching Threshold", 
                min_value=0.1, 
                max_value=0.9, 
                value=current_threshold, 
                step=0.05,
                help="Lower values = more candidates shortlisted, Higher values = stricter matching"
            )
            if new_threshold != current_threshold:
                matching_engine.set_threshold(new_threshold)
                st.success(f"✅ Threshold updated to {new_threshold:.2f}")
        
        with col2:
            st.metric("Current Threshold", f"{matching_engine.get_threshold():.2f}")
        
        # Get job requirements
        job_requirements = db_manager.get_job_requirements()
        
        if not job_requirements:
            st.warning("⚠️ No job requirements defined. Please set up job requirements first.")
        else:
            st.success("✅ Job requirements are configured")
            
            if st.button("🎯 Run Matching Algorithm", type="primary"):
                with st.spinner("Running semantic matching..."):
                    try:
                        # Get all pending candidates
                        candidates = db_manager.get_candidates_by_status('pending')
                        
                        if not candidates:
                            st.info("No pending candidates to process")
                        else:
                            # Run matching for each candidate
                            results = []
                            threshold = matching_engine.get_threshold()
                            
                            st.info(f"🔍 Processing {len(candidates)} candidates with threshold: {threshold:.2f}")
                            
                            for candidate in candidates:
                                similarity_score = matching_engine.calculate_similarity(
                                    candidate['resume_text'],
                                    job_requirements['description']
                                )
                                
                                # Determine status based on updated threshold
                                new_status = 'shortlisted' if similarity_score >= threshold else 'rejected'
                                
                                # Update candidate status
                                db_manager.update_candidate_status(candidate['id'], new_status)
                                
                                # Get detailed analysis for better insights
                                analysis = matching_engine.detailed_match_analysis(
                                    candidate['resume_text'],
                                    job_requirements['description']
                                )
                                
                                results.append({
                                    'Candidate': candidate['full_name'],
                                    'Email': candidate['email'],
                                    'Similarity Score': f"{similarity_score:.3f}",
                                    'Status': new_status.title(),
                                    'Recommendation': analysis.get('recommendation', 'No recommendation'),
                                    'Common Skills': ', '.join(analysis.get('common_terms', [])[:3])
                                })
                            
                            st.success(f"✅ Processed {len(results)} candidates")
                            
                            # Display results
                            st.subheader("Matching Results")
                            df_results = pd.DataFrame(results)
                            st.dataframe(df_results, use_container_width=True)
                            
                    except Exception as e:
                        st.error(f"Error running matching algorithm: {str(e)}")
    
    with tab2:
        st.subheader("Candidate Management")
        
        # Get all candidates
        all_candidates = db_manager.get_all_candidates()
        
        if not all_candidates:
            st.info("No candidates in the system")
        else:
            # Display candidates table
            df_candidates = pd.DataFrame(all_candidates)
            
            # Status filter
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "pending", "shortlisted", "rejected"]
            )
            
            if status_filter != "All":
                df_candidates = df_candidates[df_candidates['status'] == status_filter]
            
            st.dataframe(df_candidates, use_container_width=True)
            
            # Candidate operations
            st.subheader("Candidate Operations")
            
            # Select candidate for operations
            candidate_options = [f"{c['full_name']} ({c['email']})" for c in all_candidates]
            selected_candidate = st.selectbox("Select Candidate", candidate_options)
            
            if selected_candidate:
                selected_candidate_data = all_candidates[candidate_options.index(selected_candidate)]
                candidate_id = selected_candidate_data['id']
                
                col1, col2, col3 = st.columns(3)
                
                # Status update
                with col1:
                    st.write("**Update Status**")
                    new_status = st.selectbox("New Status", ["pending", "shortlisted", "rejected"])
                    if st.button("Update Status"):
                        db_manager.update_candidate_status(candidate_id, new_status)
                        st.success("Status updated successfully!")
                        st.rerun()
                
                # View candidate details
                with col2:
                    st.write("**View Details**")
                    if st.button("View Full Details"):
                        candidate_details = db_manager.get_candidate_details(candidate_id)
                        if candidate_details:
                            with st.expander("Candidate Details", expanded=True):
                                st.write(f"**Name:** {candidate_details['full_name']}")
                                st.write(f"**Email:** {candidate_details['email']}")
                                st.write(f"**Phone:** {candidate_details['phone']}")
                                st.write(f"**Location:** {candidate_details.get('location', 'N/A')}")
                                st.write(f"**Experience:** {candidate_details['experience_years']} years")
                                st.write(f"**Status:** {candidate_details['status']}")
                                
                                # Show education
                                if candidate_details.get('education'):
                                    st.write("**Education:**")
                                    for edu in candidate_details['education']:
                                        st.write(f"• {edu.get('degree', 'N/A')} - {edu.get('institution', 'N/A')}")
                                
                                # Show skills
                                if candidate_details.get('skills'):
                                    st.write("**Skills:**")
                                    skills_list = [skill.get('skill', 'N/A') for skill in candidate_details['skills']]
                                    st.write(", ".join(skills_list))
                                
                                # Show files
                                candidate_files = db_manager.get_candidate_files(candidate_id)
                                if candidate_files:
                                    st.write("**Files:**")
                                    for file_info in candidate_files:
                                        st.write(f"• {file_info['original_filename']} ({file_info['file_type']})")
                
                # Delete candidate
                with col3:
                    st.write("**Delete Candidate**")
                    st.warning("⚠️ This action cannot be undone!")
                    
                    # Use session state to track delete confirmation
                    delete_key = f"delete_confirm_{candidate_id}"
                    
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if not st.session_state[delete_key]:
                        if st.button("🗑️ Delete Candidate", key=f"delete_btn_{candidate_id}", type="secondary"):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        st.error("⚠️ Are you sure you want to delete this candidate?")
                        col_confirm, col_cancel = st.columns(2)
                        
                        with col_confirm:
                            if st.button("✅ Confirm Delete", key=f"confirm_delete_{candidate_id}", type="primary"):
                                if db_manager.delete_candidate(candidate_id):
                                    st.success("Candidate deleted successfully!")
                                    # Reset session state
                                    if delete_key in st.session_state:
                                        del st.session_state[delete_key]
                                    st.rerun()
                                else:
                                    st.error("Failed to delete candidate")
                                    st.session_state[delete_key] = False
                        
                        with col_cancel:
                            if st.button("❌ Cancel", key=f"cancel_delete_{candidate_id}"):
                                st.session_state[delete_key] = False
                                st.rerun()
    
    with tab3:
        st.subheader("Export Shortlisted Candidates")
        
        shortlisted = db_manager.get_candidates_by_status('shortlisted')
        
        if not shortlisted:
            st.info("No shortlisted candidates to export")
        else:
            df_shortlisted = pd.DataFrame(shortlisted)
            
            # Display preview
            st.write(f"Found {len(shortlisted)} shortlisted candidates:")
            st.dataframe(df_shortlisted, use_container_width=True)
            
            # Export options
            if st.button("📥 Download as CSV"):
                csv_buffer = io.StringIO()
                df_shortlisted.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"shortlisted_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with tab4:
        st.subheader("File Storage Management")
        
        # Storage statistics
        storage_stats = file_storage.get_storage_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Files", storage_stats['total_files'])
        col2.metric("Total Size", f"{storage_stats['total_size_mb']} MB")
        col3.metric("PDF Files", storage_stats['files_by_type'].get('PDF', {}).get('count', 0))
        col4.metric("Storage Path", "Local Folder")
        
        # File listing
        st.subheader("Stored Files")
        file_type_filter = st.selectbox("Filter by File Type", ["All", "PDF", "DOC", "DOCX", "TXT"])
        
        filter_param = None if file_type_filter == "All" else file_type_filter.lower()
        stored_files = file_storage.list_files(filter_param)
        
        if stored_files:
            files_df = pd.DataFrame(stored_files)
            st.dataframe(files_df, use_container_width=True)
            
            # File operations
            st.subheader("File Operations")
            if stored_files:
                file_options = [f"{f['filename']} ({f['file_type']})" for f in stored_files]
                selected_file = st.selectbox("Select File for Operations", file_options)
                
                if selected_file:
                    selected_file_data = stored_files[file_options.index(selected_file)]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Download File"):
                            file_content = file_storage.retrieve_file(selected_file_data['relative_path'])
                            if file_content:
                                st.download_button(
                                    label="Download",
                                    data=file_content,
                                    file_name=selected_file_data['filename'],
                                    mime="application/octet-stream"
                                )
                            else:
                                st.error("File not found")
                    
                    with col2:
                        if st.button("Archive File"):
                            if file_storage.archive_file(selected_file_data['relative_path']):
                                st.success("File archived successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to archive file")
        else:
            st.info("No files stored yet")

elif page == "View Candidates":
    st.title("👥 View All Candidates")
    
    # Get all candidates
    candidates = db_manager.get_all_candidates()
    
    if not candidates:
        st.info("No candidates registered yet")
    else:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_candidates = len(candidates)
        pending_count = len([c for c in candidates if c['status'] == 'pending'])
        shortlisted_count = len([c for c in candidates if c['status'] == 'shortlisted'])
        rejected_count = len([c for c in candidates if c['status'] == 'rejected'])
        
        col1.metric("Total Candidates", total_candidates)
        col2.metric("Pending", pending_count)
        col3.metric("Shortlisted", shortlisted_count)
        col4.metric("Rejected", rejected_count)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "pending", "shortlisted", "rejected"])
        with col2:
            sort_by = st.selectbox("Sort by", ["created_at", "full_name", "experience_years"])
        
        # Apply filters
        filtered_candidates = candidates
        if status_filter != "All":
            filtered_candidates = [c for c in filtered_candidates if c['status'] == status_filter]
        
        # Sort
        filtered_candidates.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_by == 'created_at'))
        
        # Display candidates
        for candidate in filtered_candidates:
            with st.expander(f"{candidate['full_name']} - {candidate['email']} ({candidate['status'].upper()})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Email:** {candidate['email']}")
                    st.write(f"**Phone:** {candidate['phone']}")
                    st.write(f"**Location:** {candidate.get('location', 'N/A')}")
                    st.write(f"**Experience:** {candidate['experience_years']} years")
                
                with col2:
                    st.write(f"**Status:** {candidate['status']}")
                    st.write(f"**Applied:** {candidate['created_at']}")
                
                # Show resume excerpt
                if candidate.get('resume_text'):
                    st.write("**Resume Excerpt:**")
                    st.text_area("Resume Preview", candidate['resume_text'][:500] + "...", height=100, key=f"resume_{candidate['id']}")

elif page == "Job Requirements":
    st.title("💼 Job Requirements Setup")
    
    # Get existing requirements
    existing_req = db_manager.get_job_requirements()
    
    with st.form("job_requirements_form"):
        st.subheader("Define Job Requirements")
        
        job_title = st.text_input(
            "Job Title", 
            value=existing_req.get('title', '') if existing_req else '',
            placeholder="e.g., Senior Software Engineer"
        )
        
        job_description = st.text_area(
            "Job Description & Requirements",
            value=existing_req.get('description', '') if existing_req else '',
            height=200,
            placeholder="Describe the job requirements, required skills, qualifications, etc."
        )
        
        min_experience = st.number_input(
            "Minimum Years of Experience",
            min_value=0,
            max_value=20,
            value=existing_req.get('min_experience', 0) if existing_req else 0
        )
        
        min_gpa = st.number_input(
            "Minimum GPA (optional)",
            min_value=0.0,
            max_value=4.0,
            value=existing_req.get('min_gpa', 0.0) if existing_req else 0.0,
            step=0.1
        )
        
        submit_requirements = st.form_submit_button("Save Job Requirements")
        
        if submit_requirements:
            if not job_title.strip() or not job_description.strip():
                st.error("Job title and description are required")
            else:
                try:
                    db_manager.save_job_requirements(
                        title=job_title,
                        description=job_description,
                        min_experience=min_experience,
                        min_gpa=min_gpa
                    )
                    st.success("✅ Job requirements saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving job requirements: {str(e)}")
    
    # Display current requirements
    if existing_req:
        st.subheader("Current Job Requirements")
        st.info(f"**Title:** {existing_req['title']}")
        st.info(f"**Minimum Experience:** {existing_req['min_experience']} years")
        if existing_req['min_gpa'] > 0:
            st.info(f"**Minimum GPA:** {existing_req['min_gpa']}")
        st.text_area("Description:", existing_req['description'], height=150, disabled=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Resume Shortlisting System**")
st.sidebar.markdown("Powered by Streamlit & AI")
