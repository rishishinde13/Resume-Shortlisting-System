import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import re
import string

class MatchingEngine:
    def __init__(self):
        """Initialize matching engine with TF-IDF vectorizer"""
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2),
            lowercase=True,
            token_pattern=r'\b[a-zA-Z][a-zA-Z0-9]*\b'
        )
        self.job_vector = None
        self.threshold = 0.3  # More practical threshold for real-world matching
    
    def calculate_similarity(self, resume_text: str, job_description: str) -> float:
        """
        Calculate enhanced similarity between resume and job description
        
        Args:
            resume_text: Candidate's resume text
            job_description: Job requirements text
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Preprocess texts
            resume_clean = self._preprocess_text(resume_text)
            job_clean = self._preprocess_text(job_description)
            
            if not resume_clean.strip() or not job_clean.strip():
                return 0.0
            
            # Create TF-IDF vectors
            corpus = [resume_clean, job_clean]
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            base_similarity = similarity_matrix[0][0]
            
            # Enhanced scoring with keyword matching
            keyword_boost = self._calculate_keyword_match(resume_clean, job_clean)
            
            # Weighted final score
            final_score = (base_similarity * 0.7) + (keyword_boost * 0.3)
            
            # Ensure score is between 0 and 1
            return min(max(float(final_score), 0.0), 1.0)
            
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def rank_candidates(self, candidates: List[Dict], job_description: str) -> List[Dict]:
        """
        Rank multiple candidates based on similarity to job description
        
        Args:
            candidates: List of candidate dictionaries with resume_text
            job_description: Job requirements text
            
        Returns:
            List of candidates sorted by similarity score (highest first)
        """
        try:
            if not candidates:
                return []
            
            # Calculate similarity for each candidate
            for candidate in candidates:
                resume_text = candidate.get('resume_text', '')
                similarity = self.calculate_similarity(resume_text, job_description)
                candidate['similarity_score'] = similarity
                candidate['match_status'] = 'shortlisted' if similarity >= self.threshold else 'rejected'
            
            # Sort by similarity score (descending)
            ranked_candidates = sorted(candidates, key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            return ranked_candidates
            
        except Exception as e:
            print(f"Error ranking candidates: {e}")
            return candidates
    
    def batch_similarity(self, resume_texts: List[str], job_description: str) -> List[float]:
        """
        Calculate similarity scores for multiple resumes efficiently
        
        Args:
            resume_texts: List of resume text strings
            job_description: Job requirements text
            
        Returns:
            List of similarity scores
        """
        try:
            if not resume_texts:
                return []
            
            # Preprocess all texts
            job_clean = self._preprocess_text(job_description)
            resumes_clean = [self._preprocess_text(text) for text in resume_texts]
            
            # Create corpus with job description first
            corpus = [job_clean] + resumes_clean
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            
            # Calculate similarities between job (index 0) and all resumes
            job_vector = tfidf_matrix[0:1]
            resume_vectors = tfidf_matrix[1:]
            
            similarity_scores = cosine_similarity(job_vector, resume_vectors)[0]
            
            return similarity_scores.tolist()
            
        except Exception as e:
            print(f"Error in batch similarity calculation: {e}")
            return [0.0] * len(resume_texts)
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better TF-IDF vectorization
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\.\-\+\#]', ' ', text)
        
        # Handle common programming language patterns
        text = re.sub(r'\b(c\+\+|c\#|\.net|node\.js|react\.js|vue\.js)\b', 
                     lambda m: m.group().replace('.', '').replace('+', 'plus').replace('#', 'sharp'), text)
        
        # Remove standalone numbers and very short words
        words = text.split()
        filtered_words = []
        for word in words:
            if len(word) > 1 and not word.isdigit():
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def _calculate_keyword_match(self, resume_text: str, job_text: str) -> float:
        """
        Calculate keyword matching score between resume and job description
        
        Args:
            resume_text: Processed resume text
            job_text: Processed job description text
            
        Returns:
            Keyword match score between 0 and 1
        """
        try:
            # Common technical keywords and skills
            important_keywords = [
                'python', 'java', 'javascript', 'react', 'node', 'sql', 'html', 'css',
                'aws', 'azure', 'docker', 'kubernetes', 'git', 'api', 'rest', 'json',
                'mongodb', 'postgresql', 'mysql', 'machine learning', 'ai', 'data science',
                'frontend', 'backend', 'fullstack', 'agile', 'scrum', 'ci/cd', 'devops'
            ]
            
            # Extract words from both texts
            resume_words = set(resume_text.lower().split())
            job_words = set(job_text.lower().split())
            
            # Find important keywords in job description
            job_keywords = set()
            for keyword in important_keywords:
                if keyword in job_text.lower():
                    job_keywords.add(keyword)
            
            # Also add significant words from job description
            job_significant = {word for word in job_words if len(word) > 3}
            job_keywords.update(list(job_significant)[:20])  # Top 20 significant words
            
            if not job_keywords:
                return 0.5  # Neutral score if no keywords found
            
            # Count matches in resume
            matches = 0
            for keyword in job_keywords:
                if keyword in resume_text.lower():
                    matches += 1
            
            # Calculate match percentage
            match_score = matches / len(job_keywords)
            return min(match_score, 1.0)
            
        except Exception as e:
            print(f"Error in keyword matching: {e}")
            return 0.0
    
    def extract_key_terms(self, text: str, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Extract key terms from text using TF-IDF scores
        
        Args:
            text: Text to analyze
            top_n: Number of top terms to return
            
        Returns:
            List of (term, score) tuples
        """
        try:
            cleaned_text = self._preprocess_text(text)
            
            # Fit vectorizer on the text
            tfidf_matrix = self.vectorizer.fit_transform([cleaned_text])
            
            # Get feature names and scores
            feature_names = self.vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Create term-score pairs
            term_scores = list(zip(feature_names, scores))
            
            # Sort by score and return top terms
            term_scores.sort(key=lambda x: x[1], reverse=True)
            
            return term_scores[:top_n]
            
        except Exception as e:
            print(f"Error extracting key terms: {e}")
            return []
    
    def detailed_match_analysis(self, resume_text: str, job_description: str) -> Dict:
        """
        Provide detailed analysis of match between resume and job description
        
        Args:
            resume_text: Candidate's resume text
            job_description: Job requirements text
            
        Returns:
            Dictionary with detailed match analysis
        """
        try:
            # Calculate overall similarity
            similarity_score = self.calculate_similarity(resume_text, job_description)
            
            # Extract key terms from both texts
            resume_terms = self.extract_key_terms(resume_text, 15)
            job_terms = self.extract_key_terms(job_description, 15)
            
            # Find common terms
            resume_term_set = set([term for term, score in resume_terms])
            job_term_set = set([term for term, score in job_terms])
            common_terms = resume_term_set.intersection(job_term_set)
            
            # Calculate term overlap percentage
            if job_term_set:
                term_overlap = len(common_terms) / len(job_term_set)
            else:
                term_overlap = 0.0
            
            # Determine match status
            match_status = 'shortlisted' if similarity_score >= self.threshold else 'rejected'
            
            return {
                'similarity_score': similarity_score,
                'match_status': match_status,
                'term_overlap': term_overlap,
                'common_terms': list(common_terms),
                'resume_key_terms': [term for term, score in resume_terms[:10]],
                'job_key_terms': [term for term, score in job_terms[:10]],
                'recommendation': self._get_recommendation(similarity_score, term_overlap)
            }
            
        except Exception as e:
            print(f"Error in detailed match analysis: {e}")
            return {
                'similarity_score': 0.0,
                'match_status': 'error',
                'term_overlap': 0.0,
                'common_terms': [],
                'resume_key_terms': [],
                'job_key_terms': [],
                'recommendation': 'Error in analysis'
            }
    
    def _get_recommendation(self, similarity_score: float, term_overlap: float) -> str:
        """Generate recommendation based on match scores"""
        if similarity_score >= 0.7:
            return "Excellent match - Highly recommended for interview"
        elif similarity_score >= 0.5:
            return "Good match - Recommended for interview"
        elif similarity_score >= 0.3:
            return "Moderate match - Consider for interview"
        elif similarity_score >= 0.2:
            return "Low match - Review manually before decision"
        else:
            return "Poor match - May not meet core requirements"
    
    def set_threshold(self, new_threshold: float):
        """Update the similarity threshold for shortlisting"""
        if 0.0 <= new_threshold <= 1.0:
            self.threshold = new_threshold
        else:
            raise ValueError("Threshold must be between 0.0 and 1.0")
    
    def get_threshold(self) -> float:
        """Get current similarity threshold"""
        return self.threshold
