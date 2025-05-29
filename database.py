import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

class DatabaseManager:
    def __init__(self, db_path: str = "resume_system.db"):
        """Initialize database manager with SQLite connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables with normalized schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Candidates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                location TEXT,
                experience_years INTEGER DEFAULT 0,
                resume_text TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Education table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER,
                degree TEXT,
                institution TEXT,
                graduation_year INTEGER,
                gpa REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
            )
        """)
        
        # Skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER,
                skill TEXT NOT NULL,
                proficiency_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
            )
        """)
        
        # Job requirements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                min_experience INTEGER DEFAULT 0,
                min_gpa REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # File storage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_candidate(self, full_name: str, email: str, phone: str, 
                     location: str, experience_years: int, resume_text: str,
                     education_data: List[Dict], skills_data: List[Dict], 
                     file_info: Optional[Dict] = None) -> int:
        """Add a new candidate with education and skills data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert candidate
            cursor.execute("""
                INSERT INTO candidates (full_name, email, phone, location, experience_years, resume_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (full_name, email, phone, location, experience_years, resume_text))
            
            candidate_id = cursor.lastrowid
            
            # Insert education data
            for edu in education_data:
                cursor.execute("""
                    INSERT INTO education (candidate_id, degree, institution, graduation_year, gpa)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    candidate_id,
                    edu.get('degree'),
                    edu.get('institution'),
                    edu.get('graduation_year'),
                    edu.get('gpa')
                ))
            
            # Insert skills data
            for skill in skills_data:
                cursor.execute("""
                    INSERT INTO skills (candidate_id, skill, proficiency_level)
                    VALUES (?, ?, ?)
                """, (
                    candidate_id,
                    skill.get('skill'),
                    skill.get('proficiency_level', 'Intermediate')
                ))
            
            # Insert file information if provided
            if file_info:
                cursor.execute("""
                    INSERT INTO candidate_files (candidate_id, original_filename, stored_filename, 
                                               file_path, file_type, file_size, file_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    candidate_id,
                    file_info.get('original_filename'),
                    file_info.get('stored_filename'),
                    file_info.get('relative_path'),
                    file_info.get('file_type'),
                    file_info.get('file_size'),
                    file_info.get('file_hash')
                ))
            
            conn.commit()
            return candidate_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE email = ?", (email,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count > 0
    
    def get_all_candidates(self) -> List[Dict]:
        """Get all candidates with their basic information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, full_name, email, phone, location, experience_years, 
                   status, created_at, resume_text
            FROM candidates
            ORDER BY created_at DESC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        candidates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return candidates
    
    def get_candidates_by_status(self, status: str) -> List[Dict]:
        """Get candidates filtered by status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, full_name, email, phone, location, experience_years, 
                   status, created_at, resume_text
            FROM candidates
            WHERE status = ?
            ORDER BY created_at DESC
        """, (status,))
        
        columns = [desc[0] for desc in cursor.description]
        candidates = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return candidates
    
    def update_candidate_status(self, candidate_id: int, new_status: str):
        """Update candidate status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE candidates 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, candidate_id))
        
        conn.commit()
        conn.close()
    
    def get_candidate_details(self, candidate_id: int) -> Optional[Dict]:
        """Get detailed candidate information including education and skills"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get candidate info
        cursor.execute("""
            SELECT * FROM candidates WHERE id = ?
        """, (candidate_id,))
        
        candidate_row = cursor.fetchone()
        if not candidate_row:
            conn.close()
            return None
        
        # Convert to dict
        candidate_columns = [desc[0] for desc in cursor.description]
        candidate = dict(zip(candidate_columns, candidate_row))
        
        # Get education
        cursor.execute("""
            SELECT degree, institution, graduation_year, gpa
            FROM education WHERE candidate_id = ?
        """, (candidate_id,))
        
        education = [dict(zip(['degree', 'institution', 'graduation_year', 'gpa'], row)) 
                    for row in cursor.fetchall()]
        
        # Get skills
        cursor.execute("""
            SELECT skill, proficiency_level
            FROM skills WHERE candidate_id = ?
        """, (candidate_id,))
        
        skills = [dict(zip(['skill', 'proficiency_level'], row)) 
                 for row in cursor.fetchall()]
        
        candidate['education'] = education
        candidate['skills'] = skills
        
        conn.close()
        return candidate
    
    def save_job_requirements(self, title: str, description: str, 
                            min_experience: int, min_gpa: float):
        """Save or update job requirements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing requirements (assuming single job posting)
        cursor.execute("DELETE FROM job_requirements")
        
        # Insert new requirements
        cursor.execute("""
            INSERT INTO job_requirements (title, description, min_experience, min_gpa)
            VALUES (?, ?, ?, ?)
        """, (title, description, min_experience, min_gpa))
        
        conn.commit()
        conn.close()
    
    def get_job_requirements(self) -> Optional[Dict]:
        """Get current job requirements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, description, min_experience, min_gpa, created_at
            FROM job_requirements
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['title', 'description', 'min_experience', 'min_gpa', 'created_at']
            return dict(zip(columns, row))
        
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """Get system statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total candidates
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]
        
        # Candidates by status
        cursor.execute("SELECT status, COUNT(*) FROM candidates GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_candidates': total_candidates,
            'pending': status_counts.get('pending', 0),
            'shortlisted': status_counts.get('shortlisted', 0),
            'rejected': status_counts.get('rejected', 0)
        }
    
    def delete_candidate(self, candidate_id: int) -> bool:
        """
        Delete a candidate and all associated data including files
        
        Args:
            candidate_id: ID of candidate to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get file information before deletion for cleanup
            cursor.execute("SELECT file_path FROM candidate_files WHERE candidate_id = ?", (candidate_id,))
            file_paths = [row[0] for row in cursor.fetchall()]
            
            # Delete candidate (CASCADE will handle related records)
            cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                
                # Clean up physical files
                from file_storage import FileStorageManager
                storage_manager = FileStorageManager()
                for file_path in file_paths:
                    storage_manager.delete_file(file_path)
                
                return True
            else:
                conn.close()
                return False
                
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error deleting candidate: {e}")
            return False
    
    def get_candidate_files(self, candidate_id: int) -> List[Dict]:
        """Get all files associated with a candidate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT original_filename, stored_filename, file_path, file_type, 
                   file_size, upload_date
            FROM candidate_files 
            WHERE candidate_id = ?
        """, (candidate_id,))
        
        columns = ['original_filename', 'stored_filename', 'file_path', 'file_type', 
                  'file_size', 'upload_date']
        files = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return files
