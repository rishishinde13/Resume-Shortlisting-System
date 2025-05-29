import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib
from pathlib import Path

class FileStorageManager:
    def __init__(self, storage_path: str = "resume_storage"):
        """Initialize file storage manager with local folder structure"""
        self.storage_path = Path(storage_path)
        self.setup_storage_structure()
        
        # Supported file formats
        self.supported_formats = {
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document (Modern)',
            '.txt': 'Text File'
        }
    
    def setup_storage_structure(self):
        """Create organized folder structure for file storage"""
        folders = [
            'resumes',
            'resumes/pdf',
            'resumes/doc',
            'resumes/docx', 
            'resumes/txt',
            'archived',
            'temp'
        ]
        
        for folder in folders:
            folder_path = self.storage_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ File storage structure created at: {self.storage_path}")
    
    def store_resume_file(self, file_content: bytes, original_filename: str, 
                         candidate_id: int) -> Dict[str, Any]:
        """
        Store resume file with organized naming and folder structure
        
        Args:
            file_content: File content as bytes
            original_filename: Original filename from upload
            candidate_id: Database ID of candidate
            
        Returns:
            Dictionary with file storage information
        """
        try:
            # Get file extension
            file_ext = Path(original_filename).suffix.lower()
            
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Generate unique filename with candidate ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = self._sanitize_filename(Path(original_filename).stem)
            new_filename = f"candidate_{candidate_id}_{timestamp}_{safe_filename}{file_ext}"
            
            # Determine storage folder based on file type
            storage_folder = self.storage_path / 'resumes' / file_ext[1:]  # Remove dot from extension
            file_path = storage_folder / new_filename
            
            # Store file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Generate file hash for integrity
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Get file size
            file_size = len(file_content)
            
            storage_info = {
                'stored_filename': new_filename,
                'storage_path': str(file_path),
                'relative_path': str(file_path.relative_to(self.storage_path)),
                'original_filename': original_filename,
                'file_size': file_size,
                'file_hash': file_hash,
                'file_type': self.supported_formats[file_ext],
                'stored_at': datetime.now().isoformat()
            }
            
            print(f"✓ File stored: {new_filename} ({file_size} bytes)")
            return storage_info
            
        except Exception as e:
            raise Exception(f"Failed to store file: {str(e)}")
    
    def retrieve_file(self, file_path: str) -> Optional[bytes]:
        """
        Retrieve file content from storage
        
        Args:
            file_path: Path to stored file
            
        Returns:
            File content as bytes or None if not found
        """
        try:
            full_path = self.storage_path / file_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"Error retrieving file: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            full_path = self.storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                print(f"✓ File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def archive_file(self, file_path: str) -> bool:
        """
        Move file to archived folder instead of deleting
        
        Args:
            file_path: Path to file to archive
            
        Returns:
            True if archived successfully, False otherwise
        """
        try:
            source_path = self.storage_path / file_path
            if source_path.exists():
                archive_path = self.storage_path / 'archived' / source_path.name
                shutil.move(str(source_path), str(archive_path))
                print(f"✓ File archived: {file_path}")
                return True
            return False
        except Exception as e:
            print(f"Error archiving file: {e}")
            return False
    
    def list_files(self, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all stored files with metadata
        
        Args:
            file_type: Filter by file type (pdf, doc, docx, txt)
            
        Returns:
            List of file information dictionaries
        """
        files = []
        try:
            resumes_path = self.storage_path / 'resumes'
            
            folders_to_scan = [file_type] if file_type else ['pdf', 'doc', 'docx', 'txt']
            
            for folder in folders_to_scan:
                folder_path = resumes_path / folder
                if folder_path.exists():
                    for file_path in folder_path.glob('*'):
                        if file_path.is_file():
                            stat = file_path.stat()
                            files.append({
                                'filename': file_path.name,
                                'relative_path': str(file_path.relative_to(self.storage_path)),
                                'file_type': folder.upper(),
                                'file_size': stat.st_size,
                                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
            
            return sorted(files, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        stats = {
            'total_files': 0,
            'total_size': 0,
            'files_by_type': {},
            'storage_path': str(self.storage_path)
        }
        
        try:
            files = self.list_files()
            stats['total_files'] = len(files)
            
            for file_info in files:
                file_type = file_info['file_type']
                file_size = file_info['file_size']
                
                stats['total_size'] += file_size
                
                if file_type not in stats['files_by_type']:
                    stats['files_by_type'][file_type] = {'count': 0, 'size': 0}
                
                stats['files_by_type'][file_type]['count'] += 1
                stats['files_by_type'][file_type]['size'] += file_size
            
            # Convert bytes to MB for readability
            stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return stats
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        sanitized = filename
        
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove multiple underscores and trim
        sanitized = '_'.join(sanitized.split('_'))
        sanitized = sanitized.strip('_')
        
        # Limit length
        return sanitized[:50] if len(sanitized) > 50 else sanitized
    
    def validate_file_format(self, filename: str) -> bool:
        """
        Validate if file format is supported
        
        Args:
            filename: Name of file to validate
            
        Returns:
            True if format is supported, False otherwise
        """
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.supported_formats
    
    def get_supported_formats(self) -> Dict[str, str]:
        """
        Get list of supported file formats
        
        Returns:
            Dictionary mapping extensions to descriptions
        """
        return self.supported_formats.copy()