import fitz  # PyMuPDF
import re
from typing import Optional, Dict, Any
import io

class PDFParser:
    def __init__(self):
        """Initialize PDF parser using PyMuPDF with Groq enhancement"""
        self.groq_processor = None
        try:
            from groq_processor import GroqProcessor
            self.groq_processor = GroqProcessor()
            print("✓ PDF parser enhanced with Groq LLM for better text processing")
        except Exception as e:
            print(f"Note: PDF parser using basic extraction only: {e}")
            pass
    
    def extract_text(self, pdf_content: bytes) -> str:
        """
        Extract text content from PDF bytes using PyMuPDF
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text as string
        """
        try:
            # Create a PyMuPDF document from bytes
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            
            extracted_text = ""
            
            # Iterate through all pages
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Extract text from the page
                page_text = page.get_text()
                
                # Clean and normalize the text
                page_text = self._clean_text(page_text)
                extracted_text += page_text + "\n"
            
            pdf_document.close()
            
            # Enhance text with Groq if available
            if self.groq_processor and extracted_text.strip():
                try:
                    enhanced_text = self.groq_processor.enhance_resume_text(extracted_text)
                    print("✓ Resume text enhanced with Groq LLM for better semantic analysis")
                    return enhanced_text
                except Exception as e:
                    print(f"Note: Using basic text extraction: {e}")
            
            return extracted_text.strip()
            
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\-\(\)\@\+\/\&\%\$\#\!\?\:\;]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_metadata(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Extract PDF metadata
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            
            metadata = {
                'page_count': pdf_document.page_count,
                'title': pdf_document.metadata.get('title', ''),
                'author': pdf_document.metadata.get('author', ''),
                'subject': pdf_document.metadata.get('subject', ''),
                'creator': pdf_document.metadata.get('creator', ''),
                'producer': pdf_document.metadata.get('producer', ''),
                'creation_date': pdf_document.metadata.get('creationDate', ''),
                'modification_date': pdf_document.metadata.get('modDate', '')
            }
            
            pdf_document.close()
            
            return metadata
            
        except Exception as e:
            return {'error': f"Failed to extract metadata: {str(e)}"}
    
    def validate_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Validate PDF file and return validation results
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Dictionary containing validation results
        """
        try:
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            
            # Basic validation
            is_valid = True
            messages = []
            
            # Check if PDF can be opened
            if pdf_document.page_count == 0:
                is_valid = False
                messages.append("PDF has no pages")
            
            # Check if text can be extracted
            try:
                first_page = pdf_document[0]
                first_page_text = first_page.get_text()
                
                if not first_page_text.strip():
                    messages.append("Warning: No text found on first page - might be image-based PDF")
                
            except Exception:
                is_valid = False
                messages.append("Cannot extract text from PDF")
            
            pdf_document.close()
            
            return {
                'is_valid': is_valid,
                'messages': messages,
                'page_count': pdf_document.page_count if is_valid else 0
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'messages': [f"PDF validation failed: {str(e)}"],
                'page_count': 0
            }
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Attempt to identify and extract common resume sections
        
        Args:
            text: Extracted resume text
            
        Returns:
            Dictionary with identified sections
        """
        sections = {
            'contact': '',
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'other': ''
        }
        
        try:
            # Convert to lowercase for pattern matching
            text_lower = text.lower()
            
            # Define section keywords
            section_patterns = {
                'experience': r'(experience|work history|employment|professional experience)',
                'education': r'(education|academic|qualifications|degrees)',
                'skills': r'(skills|technical skills|competencies|expertise)',
                'summary': r'(summary|objective|profile|about)'
            }
            
            # Find section positions
            section_positions = {}
            for section_name, pattern in section_patterns.items():
                match = re.search(pattern, text_lower)
                if match:
                    section_positions[section_name] = match.start()
            
            # Sort sections by position
            sorted_sections = sorted(section_positions.items(), key=lambda x: x[1])
            
            # Extract content between sections
            for i, (section_name, start_pos) in enumerate(sorted_sections):
                if i < len(sorted_sections) - 1:
                    end_pos = sorted_sections[i + 1][1]
                    section_content = text[start_pos:end_pos].strip()
                else:
                    section_content = text[start_pos:].strip()
                
                sections[section_name] = section_content
            
            return sections
            
        except Exception:
            # If section extraction fails, return original text in 'other'
            sections['other'] = text
            return sections
