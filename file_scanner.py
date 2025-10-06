"""
File Scanner for Automatic CSV Detection

Scans predefined folders for CSV files and tracks processing status
to enable automatic file loading without manual uploads.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd


class FileScanner:
    """Scans folders for CSV/Excel files and tracks their processing status."""
    
    def __init__(self, tracking_file: str = "file_tracking.json"):
        """
        Initialize the file scanner.
        
        Args:
            tracking_file: Path to JSON file that tracks processed files
        """
        self.tracking_file = tracking_file
        self.processed_files = self._load_tracking()
    
    def _load_tracking(self) -> Dict:
        """Load the file tracking database from JSON."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading tracking file: {e}")
                return {}
        return {}
    
    def _save_tracking(self):
        """Save the file tracking database to JSON."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.processed_files, f, indent=2)
        except Exception as e:
            print(f"Error saving tracking file: {e}")
    
    def scan_folders(self, folder_paths: List[str]) -> List[Dict]:
        """
        Scan multiple folders for CSV and Excel files.
        
        Args:
            folder_paths: List of folder paths to scan
            
        Returns:
            List of file information dictionaries with:
                - path: Full file path
                - filename: File name
                - folder: Parent folder name
                - size_mb: File size in MB
                - modified: Last modified timestamp
                - status: 'new', 'processed', or 'error'
                - last_processed: Timestamp of last processing (if applicable)
        """
        files = []
        
        for folder_path in folder_paths:
            if not os.path.exists(folder_path):
                print(f"Warning: Folder not found: {folder_path}")
                continue
            
            try:
                # Get all CSV and Excel files in the folder
                for filename in os.listdir(folder_path):
                    if filename.endswith(('.csv', '.xlsx', '.xls')):
                        file_path = os.path.join(folder_path, filename)
                        
                        # Skip if it's a directory
                        if os.path.isdir(file_path):
                            continue
                        
                        # Get file info
                        try:
                            file_stat = os.stat(file_path)
                            size_mb = file_stat.st_size / (1024 * 1024)
                            modified = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            # Check processing status
                            file_key = self._get_file_key(file_path)
                            
                            if file_key in self.processed_files:
                                file_info = self.processed_files[file_key]
                                # Check if file was modified since last processing
                                if file_info.get('modified') == modified.isoformat():
                                    status = 'processed'
                                else:
                                    status = 'modified'
                                last_processed = file_info.get('processed_at', 'Unknown')
                            else:
                                status = 'new'
                                last_processed = None
                            
                            files.append({
                                'path': file_path,
                                'filename': filename,
                                'folder': os.path.basename(folder_path),
                                'size_mb': round(size_mb, 2),
                                'modified': modified.isoformat(),
                                'status': status,
                                'last_processed': last_processed
                            })
                        
                        except Exception as e:
                            print(f"Error getting info for {filename}: {e}")
                            files.append({
                                'path': file_path,
                                'filename': filename,
                                'folder': os.path.basename(folder_path),
                                'size_mb': 0,
                                'modified': None,
                                'status': 'error',
                                'last_processed': None,
                                'error': str(e)
                            })
            
            except Exception as e:
                print(f"Error scanning folder {folder_path}: {e}")
        
        return files
    
    def _get_file_key(self, file_path: str) -> str:
        """Generate a unique key for a file based on its absolute path."""
        return os.path.abspath(file_path)
    
    def mark_processed(self, file_path: str, success: bool = True, 
                      records_count: int = 0, error: str = None):
        """
        Mark a file as processed in the tracking database.
        
        Args:
            file_path: Path to the file
            success: Whether processing was successful
            records_count: Number of records processed
            error: Error message if processing failed
        """
        file_key = self._get_file_key(file_path)
        
        try:
            file_stat = os.stat(file_path)
            modified = datetime.fromtimestamp(file_stat.st_mtime)
            
            self.processed_files[file_key] = {
                'filename': os.path.basename(file_path),
                'processed_at': datetime.now().isoformat(),
                'modified': modified.isoformat(),
                'success': success,
                'records_count': records_count,
                'error': error
            }
            
            self._save_tracking()
        
        except Exception as e:
            print(f"Error marking file as processed: {e}")
    
    def get_new_files(self, folder_paths: List[str]) -> List[Dict]:
        """
        Get only new or modified files that haven't been processed.
        
        Args:
            folder_paths: List of folder paths to scan
            
        Returns:
            List of new/modified file information
        """
        all_files = self.scan_folders(folder_paths)
        return [f for f in all_files if f['status'] in ['new', 'modified']]
    
    def reset_file_status(self, file_path: str):
        """
        Reset the processing status of a file.
        
        Args:
            file_path: Path to the file to reset
        """
        file_key = self._get_file_key(file_path)
        if file_key in self.processed_files:
            del self.processed_files[file_key]
            self._save_tracking()
    
    def get_file_stats(self) -> Dict:
        """
        Get statistics about tracked files.
        
        Returns:
            Dictionary with processing statistics
        """
        successful = sum(1 for f in self.processed_files.values() if f.get('success', False))
        failed = sum(1 for f in self.processed_files.values() if not f.get('success', True))
        total_records = sum(f.get('records_count', 0) for f in self.processed_files.values())
        
        return {
            'total_tracked': len(self.processed_files),
            'successful': successful,
            'failed': failed,
            'total_records_processed': total_records
        }
