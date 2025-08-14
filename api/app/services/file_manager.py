import os
import hashlib
import shutil
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManager:
    """Service for managing file uploads, persistence, and hash tracking"""
    
    def __init__(self):
        self.docs_dir = "/app/data/docs"
        self.manifest_file = "/app/data/docs/.file_manifest.json"
        self.manifest = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Any]:
        """Load the file manifest from disk"""
        try:
            if os.path.exists(self.manifest_file):
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            else:
                return {"files": {}, "last_updated": None}
        except Exception as e:
            logger.error(f"Error loading manifest: {e}")
            return {"files": {}, "last_updated": None}
    
    def _save_manifest(self):
        """Save the file manifest to disk"""
        try:
            # Ensure docs directory exists
            os.makedirs(self.docs_dir, exist_ok=True)
            
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=2)
            logger.info("File manifest saved successfully")
        except Exception as e:
            logger.error(f"Error saving manifest: {e}")
    
    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information including hash and metadata"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            stat = os.stat(file_path)
            file_hash = self.compute_file_hash(file_path)
            
            return {
                "filename": os.path.basename(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "hash": file_hash,
                "path": file_path
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def is_file_changed(self, file_path: str, filename: str) -> bool:
        """Check if a file has changed based on hash comparison"""
        if filename not in self.manifest["files"]:
            return True  # New file
        
        stored_hash = self.manifest["files"][filename]["hash"]
        current_hash = self.compute_file_hash(file_path)
        
        return stored_hash != current_hash
    
    def save_uploaded_file(self, uploaded_file, filename: str) -> Dict[str, Any]:
        """Save an uploaded file and track its hash"""
        try:
            # Ensure docs directory exists
            os.makedirs(self.docs_dir, exist_ok=True)
            
            # Generate unique filename if duplicate exists
            base_name, ext = os.path.splitext(filename)
            counter = 1
            final_filename = filename
            
            while os.path.exists(os.path.join(self.docs_dir, final_filename)):
                final_filename = f"{base_name}_{counter}{ext}"
                counter += 1
            
            # Save the file
            file_path = os.path.join(self.docs_dir, final_filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(uploaded_file.file, buffer)
            
            # Get file info and hash
            file_info = self.get_file_info(file_path)
            
            # Update manifest
            self.manifest["files"][final_filename] = {
                "hash": file_info["hash"],
                "size": file_info["size"],
                "modified": file_info["modified"],
                "uploaded_at": file_info["modified"]
            }
            self.manifest["last_updated"] = file_info["modified"]
            
            # Save manifest
            self._save_manifest()
            
            logger.info(f"File {final_filename} saved successfully with hash {file_info['hash']}")
            
            return {
                "success": True,
                "filename": final_filename,
                "hash": file_info["hash"],
                "size": file_info["size"],
                "message": "File uploaded and saved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error saving uploaded file {filename}: {e}")
            return {
                "success": False,
                "filename": filename,
                "error": str(e),
                "message": "Failed to save uploaded file"
            }
    
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get information about all tracked files"""
        files = []
        for filename, info in self.manifest["files"].items():
            file_path = os.path.join(self.docs_dir, filename)
            if os.path.exists(file_path):
                files.append({
                    "filename": filename,
                    "hash": info["hash"],
                    "size": info["size"],
                    "modified": info["modified"],
                    "uploaded_at": info["uploaded_at"]
                })
            else:
                # File no longer exists, remove from manifest
                del self.manifest["files"][filename]
        
        # Save updated manifest if files were removed
        if len(files) != len(self.manifest["files"]):
            self._save_manifest()
        
        return files
    
    def get_kb_status(self) -> Dict[str, Any]:
        """Get knowledge base status information"""
        files = self.get_all_files()
        
        return {
            "docs_count": len(files),
            "docs": files,
            "index_ready": len(files) > 0,
            "last_updated": self.manifest.get("last_updated"),
            "manifest_file": self.manifest_file
        }
    
    def refresh_manifest(self) -> Dict[str, Any]:
        """Refresh the file manifest by scanning the docs directory"""
        try:
            # Scan docs directory for files
            if not os.path.exists(self.docs_dir):
                return {"success": False, "message": "Docs directory does not exist"}
            
            scanned_files = []
            for filename in os.listdir(self.docs_dir):
                if filename.startswith('.'):  # Skip hidden files
                    continue
                
                file_path = os.path.join(self.docs_dir, filename)
                if os.path.isfile(file_path):
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        scanned_files.append(file_info)
            
            # Update manifest with new files
            new_files = 0
            for file_info in scanned_files:
                filename = file_info["filename"]
                if filename not in self.manifest["files"]:
                    self.manifest["files"][filename] = {
                        "hash": file_info["hash"],
                        "size": file_info["size"],
                        "modified": file_info["modified"],
                        "uploaded_at": file_info["modified"]
                    }
                    new_files += 1
                elif self.manifest["files"][filename]["hash"] != file_info["hash"]:
                    # File changed, update hash
                    self.manifest["files"][filename]["hash"] = file_info["hash"]
                    self.manifest["files"][filename]["modified"] = file_info["modified"]
                    new_files += 1
            
            if new_files > 0:
                self.manifest["last_updated"] = max(f["modified"] for f in scanned_files)
                self._save_manifest()
            
            return {
                "success": True,
                "message": f"Manifest refreshed, {new_files} files updated",
                "new_files": new_files,
                "total_files": len(scanned_files)
            }
            
        except Exception as e:
            logger.error(f"Error refreshing manifest: {e}")
            return {"success": False, "error": str(e), "message": "Failed to refresh manifest"}
    
    def update_file_manifest(self, file_path: str, content: str) -> Dict[str, Any]:
        """Update the file manifest with a new or updated file"""
        try:
            filename = os.path.basename(file_path)
            
            # Calculate hash of content
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Get file info
            file_info = {
                "filename": filename,
                "hash": content_hash,
                "size": len(content.encode('utf-8')),
                "modified": datetime.utcnow().isoformat(),
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            # Update manifest
            self.manifest["files"][filename] = file_info
            self.manifest["last_updated"] = file_info["modified"]
            
            # Save manifest
            self._save_manifest()
            
            return {
                "success": True,
                "message": f"File manifest updated for {filename}",
                "file_info": file_info
            }
            
        except Exception as e:
            logger.error(f"Error updating file manifest: {e}")
            return {"success": False, "error": str(e), "message": "Failed to update file manifest"}
    
    def cleanup_orphaned_files(self) -> Dict[str, Any]:
        """Remove files from manifest that no longer exist on disk"""
        try:
            orphaned_count = 0
            for filename in list(self.manifest["files"].keys()):
                file_path = os.path.join(self.docs_dir, filename)
                if not os.path.exists(file_path):
                    del self.manifest["files"][filename]
                    orphaned_count += 1
            
            if orphaned_count > 0:
                self._save_manifest()
            
            return {
                "success": True,
                "message": f"Cleaned up {orphaned_count} orphaned files",
                "orphaned_count": orphaned_count
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned files: {e}")
            return {"success": False, "error": str(e), "message": "Failed to cleanup orphaned files"}
