import os
import json
from groq import Groq
from typing import Dict, List, Tuple, Optional
import re

class GroqProcessor:
    def __init__(self):
        """Initialize Groq processor with API client"""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama3-8b-8192"  # Fast and efficient model
    
    def structure_resume_data(self, raw_text: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Use Groq LLM to structure raw resume text into education and skills data
        
        Args:
            raw_text: Raw extracted text from PDF
            
        Returns:
            Tuple of (education_data, skills_data)
        """
        try:
            # Create a structured prompt for the LLM
            prompt = self._create_resume_parsing_prompt(raw_text)
            
            # Get response from Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume parser. Extract structured data from resumes and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent output
                max_tokens=2048
            )
            
            # Parse the response
            response_content = response.choices[0].message.content or ""
            structured_data = self._parse_llm_response(response_content)
            
            education_data = structured_data.get('education', [])
            skills_data = structured_data.get('skills', [])
            
            return education_data, skills_data
            
        except Exception as e:
            print(f"Error processing with Groq: {e}")
            # Fallback to basic extraction if LLM fails
            return self._fallback_extraction(raw_text)
    
    def _create_resume_parsing_prompt(self, text: str) -> str:
        """Create a structured prompt for resume parsing"""
        prompt = f"""
Parse the following resume text and extract structured information. Return ONLY a valid JSON object with the exact structure shown below:

{{
    "education": [
        {{
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University Name",
            "graduation_year": 2020,
            "gpa": 3.8
        }}
    ],
    "skills": [
        {{
            "skill": "Python",
            "proficiency_level": "Advanced"
        }},
        {{
            "skill": "JavaScript",
            "proficiency_level": "Intermediate"
        }}
    ]
}}

Instructions:
1. Extract all educational qualifications (degrees, certifications, courses)
2. Extract technical and professional skills
3. For education: include degree type, institution name, graduation year (if mentioned), and GPA (if mentioned)
4. For skills: categorize proficiency as "Beginner", "Intermediate", "Advanced", or "Expert" based on context
5. If information is not available, use null for that field
6. Only include relevant technical skills, programming languages, tools, and professional competencies
7. Return ONLY the JSON object, no additional text or explanation

Resume Text:
{text}
"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse and validate LLM response"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                # Validate structure
                if self._validate_structure(parsed_data):
                    return parsed_data
            
            # If parsing fails, return empty structure
            return {"education": [], "skills": []}
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {"education": [], "skills": []}
    
    def _validate_structure(self, data: Dict) -> bool:
        """Validate the structure of parsed data"""
        try:
            # Check if required keys exist
            if 'education' not in data or 'skills' not in data:
                return False
            
            # Validate education entries
            for edu in data['education']:
                if not isinstance(edu, dict):
                    return False
                # Check for required education fields
                required_edu_fields = ['degree', 'institution', 'graduation_year', 'gpa']
                for field in required_edu_fields:
                    if field not in edu:
                        edu[field] = None
            
            # Validate skills entries
            for skill in data['skills']:
                if not isinstance(skill, dict):
                    return False
                # Check for required skill fields
                if 'skill' not in skill:
                    return False
                if 'proficiency_level' not in skill:
                    skill['proficiency_level'] = 'Intermediate'
            
            return True
            
        except Exception:
            return False
    
    def _fallback_extraction(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """Fallback extraction method if LLM fails"""
        education_data = []
        skills_data = []
        
        try:
            # Basic education extraction
            if any(keyword in text.lower() for keyword in ['degree', 'bachelor', 'master', 'university', 'college']):
                education_data.append({
                    'degree': 'Degree mentioned in resume',
                    'institution': None,
                    'graduation_year': None,
                    'gpa': None
                })
            
            # Basic skills extraction
            common_skills = [
                'python', 'java', 'javascript', 'react', 'node', 'sql', 'html', 'css',
                'git', 'docker', 'aws', 'azure', 'mongodb', 'postgresql', 'mysql'
            ]
            
            text_lower = text.lower()
            found_skills = []
            for skill in common_skills:
                if skill in text_lower:
                    found_skills.append({
                        'skill': skill.title(),
                        'proficiency_level': 'Intermediate'
                    })
            
            skills_data = found_skills
            
        except Exception as e:
            print(f"Fallback extraction error: {e}")
        
        return education_data, skills_data
    
    def enhance_resume_text(self, raw_text: str) -> str:
        """
        Use Groq to clean and enhance resume text for better vectorization
        
        Args:
            raw_text: Raw extracted text from PDF
            
        Returns:
            Cleaned and enhanced text
        """
        try:
            prompt = f"""
Clean and enhance the following resume text for semantic analysis. 
Remove formatting artifacts, fix broken words, and standardize terminology.
Return only the cleaned text without any additional formatting or explanations.

Original Text:
{raw_text}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a text cleaning expert. Clean and enhance resume text for better analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            enhanced_text = response.choices[0].message.content
            if enhanced_text:
                return enhanced_text.strip()
            return raw_text
            
        except Exception as e:
            print(f"Error enhancing text with Groq: {e}")
            return raw_text
    
    def extract_contact_info(self, raw_text: str) -> Dict[str, Optional[str]]:
        """
        Extract contact information using Groq LLM
        
        Args:
            raw_text: Raw extracted text from PDF
            
        Returns:
            Dictionary with contact information
        """
        try:
            prompt = f"""
Extract contact information from the following resume text and return ONLY a valid JSON object:

{{
    "email": "example@email.com",
    "phone": "+1-234-567-8900",
    "location": "City, State",
    "linkedin": "linkedin.com/in/profile",
    "name": "Full Name"
}}

Instructions:
1. Extract email address, phone number, location, LinkedIn profile, and full name
2. Use null for any information not found
3. Return ONLY the JSON object, no additional text

Resume Text:
{raw_text}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting contact information from resumes. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=512
            )
            
            # Parse response
            response_content = response.choices[0].message.content
            if not response_content:
                return {}
            
            response_text = response_content.strip()
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                contact_info = json.loads(json_match.group())
                return contact_info
            
            return {}
            
        except Exception as e:
            print(f"Error extracting contact info: {e}")
            return {}