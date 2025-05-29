import spacy
import re
from typing import List, Dict, Tuple, Optional
import string
from groq_processor import GroqProcessor

class NLPProcessor:
    def __init__(self):
        """Initialize NLP processor with spaCy model and Groq LLM"""
        try:
            # Try to load the English model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # If model is not available, create a minimal processor
            print("Warning: spaCy English model not found. Using basic text processing.")
            self.nlp = None
        
        # Initialize Groq processor for advanced text processing
        try:
            self.groq_processor = GroqProcessor()
            print("✓ Groq LLM integration enabled for enhanced resume parsing")
        except Exception as e:
            print(f"Warning: Groq processor initialization failed: {e}")
            self.groq_processor = None
        
        # Define common degree patterns
        self.degree_patterns = [
            r'\b(bachelor|bachelors|ba|bs|bsc|be|btech|beng)\b',
            r'\b(master|masters|ma|ms|msc|mba|mtech|meng)\b',
            r'\b(phd|ph\.d|doctorate|doctoral)\b',
            r'\b(associate|diploma|certificate)\b'
        ]
        
        # Define common skill categories
        self.skill_keywords = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'kotlin', 'swift'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'bootstrap'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform'],
            'tools': ['git', 'jira', 'confluence', 'slack', 'figma', 'photoshop', 'excel'],
            'frameworks': ['spring', 'hibernate', 'laravel', 'rails', 'asp.net', 'xamarin']
        }
    
    def extract_entities(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract education and skills entities from resume text using Groq LLM
        
        Args:
            text: Resume text content
            
        Returns:
            Tuple of (education_data, skills_data)
        """
        # Try using Groq LLM for better structured extraction
        if self.groq_processor:
            try:
                print("🤖 Using Groq LLM for enhanced resume parsing...")
                education_data, skills_data = self.groq_processor.structure_resume_data(text)
                
                # Validate the results
                if education_data or skills_data:
                    print(f"✓ Groq extracted {len(education_data)} education entries and {len(skills_data)} skills")
                    return education_data, skills_data
                else:
                    print("⚠️ Groq extraction returned empty results, falling back to basic parsing")
            except Exception as e:
                print(f"⚠️ Groq processing failed: {e}, using fallback extraction")
        
        # Fallback to basic extraction if Groq is not available or fails
        print("📝 Using basic pattern-based extraction...")
        education_data = self._extract_education(text)
        skills_data = self._extract_skills(text)
        
        return education_data, skills_data
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information from text"""
        education_entries = []
        
        try:
            # Convert to lowercase for pattern matching
            text_lower = text.lower()
            
            # Find education section
            education_section = self._find_education_section(text)
            if education_section:
                text_to_process = education_section
            else:
                text_to_process = text
            
            # Extract degrees
            degrees = self._extract_degrees(text_to_process)
            
            # Extract institutions
            institutions = self._extract_institutions(text_to_process)
            
            # Extract years
            years = self._extract_graduation_years(text_to_process)
            
            # Extract GPA if mentioned
            gpa = self._extract_gpa(text_to_process)
            
            # Combine information
            max_entries = max(len(degrees), len(institutions), 1)
            
            for i in range(max_entries):
                entry = {
                    'degree': degrees[i] if i < len(degrees) else None,
                    'institution': institutions[i] if i < len(institutions) else None,
                    'graduation_year': years[i] if i < len(years) else None,
                    'gpa': gpa[i] if i < len(gpa) else None
                }
                
                # Only add if we have at least degree or institution
                if entry['degree'] or entry['institution']:
                    education_entries.append(entry)
            
            # If no structured data found, try to extract any educational keywords
            if not education_entries:
                fallback_education = self._extract_education_fallback(text)
                if fallback_education:
                    education_entries.extend(fallback_education)
                    
        except Exception as e:
            print(f"Error extracting education: {e}")
        
        return education_entries
    
    def _extract_skills(self, text: str) -> List[Dict]:
        """Extract skills from text"""
        skills_data = []
        
        try:
            # Convert to lowercase for matching
            text_lower = text.lower()
            
            # Remove punctuation for better matching
            text_clean = text_lower.translate(str.maketrans('', '', string.punctuation))
            
            # Find all skill matches
            found_skills = set()
            
            for category, skills in self.skill_keywords.items():
                for skill in skills:
                    # Check for exact word matches
                    if re.search(r'\b' + re.escape(skill) + r'\b', text_clean):
                        found_skills.add(skill.title())
            
            # Additional pattern-based skill extraction
            additional_skills = self._extract_additional_skills(text)
            found_skills.update(additional_skills)
            
            # Convert to list of dictionaries
            for skill in found_skills:
                skills_data.append({
                    'skill': skill,
                    'proficiency_level': 'Intermediate'  # Default proficiency
                })
            
            # If using spaCy, try to extract using NER
            if self.nlp:
                spacy_skills = self._extract_skills_with_spacy(text)
                for skill in spacy_skills:
                    if skill not in found_skills:
                        skills_data.append({
                            'skill': skill,
                            'proficiency_level': 'Intermediate'
                        })
        
        except Exception as e:
            print(f"Error extracting skills: {e}")
        
        return skills_data
    
    def _find_education_section(self, text: str) -> Optional[str]:
        """Find and extract education section from text"""
        text_lower = text.lower()
        
        # Look for education section headers
        education_patterns = [
            r'education',
            r'academic background',
            r'qualifications',
            r'educational background'
        ]
        
        for pattern in education_patterns:
            match = re.search(pattern, text_lower)
            if match:
                start_pos = match.start()
                
                # Find the end of the section (next major section)
                next_section_patterns = [
                    r'experience',
                    r'work history',
                    r'employment',
                    r'skills',
                    r'projects',
                    r'achievements'
                ]
                
                end_pos = len(text)
                for next_pattern in next_section_patterns:
                    next_match = re.search(next_pattern, text_lower[start_pos + 100:])
                    if next_match:
                        end_pos = start_pos + 100 + next_match.start()
                        break
                
                return text[start_pos:end_pos]
        
        return None
    
    def _extract_degrees(self, text: str) -> List[str]:
        """Extract degree information"""
        degrees = []
        text_lower = text.lower()
        
        for pattern in self.degree_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Extract some context around the match
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Clean up and add to degrees
                degree = re.sub(r'\s+', ' ', context)
                if degree not in degrees:
                    degrees.append(degree)
        
        return degrees
    
    def _extract_institutions(self, text: str) -> List[str]:
        """Extract institution names"""
        institutions = []
        
        # Common university/college keywords
        institution_patterns = [
            r'\b\w+\s+university\b',
            r'\b\w+\s+college\b',
            r'\b\w+\s+institute\b',
            r'\b\w+\s+school\b'
        ]
        
        for pattern in institution_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                institution = match.group().strip()
                if institution not in institutions:
                    institutions.append(institution)
        
        return institutions
    
    def _extract_graduation_years(self, text: str) -> List[int]:
        """Extract graduation years"""
        years = []
        
        # Look for 4-digit years between 1980 and current year + 5
        year_pattern = r'\b(19[8-9]\d|20[0-3]\d)\b'
        matches = re.finditer(year_pattern, text)
        
        for match in matches:
            year = int(match.group())
            if 1980 <= year <= 2030:  # Reasonable range for graduation years
                years.append(year)
        
        return sorted(set(years))  # Remove duplicates and sort
    
    def _extract_gpa(self, text: str) -> List[float]:
        """Extract GPA information"""
        gpas = []
        
        # Look for GPA patterns
        gpa_patterns = [
            r'gpa[\s:]*(\d+\.?\d*)',
            r'grade point average[\s:]*(\d+\.?\d*)',
            r'cgpa[\s:]*(\d+\.?\d*)'
        ]
        
        for pattern in gpa_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    gpa = float(match.group(1))
                    if 0.0 <= gpa <= 4.0:  # Reasonable GPA range
                        gpas.append(gpa)
                except ValueError:
                    continue
        
        return gpas
    
    def _extract_education_fallback(self, text: str) -> List[Dict]:
        """Fallback method to extract any educational keywords"""
        education_entries = []
        
        # Common educational terms
        edu_keywords = ['degree', 'bachelor', 'master', 'phd', 'university', 'college', 'graduation']
        
        found_terms = []
        for keyword in edu_keywords:
            if keyword.lower() in text.lower():
                found_terms.append(keyword)
        
        if found_terms:
            education_entries.append({
                'degree': ', '.join(found_terms),
                'institution': None,
                'graduation_year': None,
                'gpa': None
            })
        
        return education_entries
    
    def _extract_additional_skills(self, text: str) -> set:
        """Extract additional skills using pattern matching"""
        skills = set()
        
        # Look for skill-like patterns
        skill_patterns = [
            r'\b[A-Z]{2,8}\b',  # Acronyms (e.g., API, REST, JSON)
            r'\b\w+\.\w+\b',    # Dotted technologies (e.g., React.js, Node.js)
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                potential_skill = match.group()
                # Filter out common non-skill acronyms
                if len(potential_skill) > 1 and potential_skill.upper() not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAS', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BUT', 'HAVE']:
                    skills.add(potential_skill)
        
        return skills
    
    def _extract_skills_with_spacy(self, text: str) -> List[str]:
        """Extract skills using spaCy NER if available"""
        if not self.nlp:
            return []
        
        skills = []
        
        try:
            doc = self.nlp(text)
            
            # Extract entities that might be skills
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'WORK_OF_ART']:
                    # Filter for potential technology/skill names
                    if len(ent.text) > 1 and not ent.text.isdigit():
                        skills.append(ent.text)
        
        except Exception as e:
            print(f"Error with spaCy processing: {e}")
        
        return skills
