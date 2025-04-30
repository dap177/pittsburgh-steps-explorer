#!/usr/bin/env python
"""
Pittsburgh Steps Explorer - Automated Backup Script
This script creates backups of all critical application data.
Run it manually or set up as a scheduled task.
"""

import os
import json
import shutil
import datetime
from google.cloud import storage
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BACKUP_DIR = "backups"
GCS_BUCKET = "pittsburgh-steps-uploads"
GCS_BACKUP_PATH = "backups"
LOCAL_FILES_TO_BACKUP = [
    "Pittsburgh_Steps.geojson",
    "user_contributions.json"
]

def ensure_backup_dir():
    """Create backup directory if it doesn't exist"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Created backup directory: {BACKUP_DIR}")

def backup_local_files():
    """Backup local data files"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subdir = os.path.join(BACKUP_DIR, timestamp)
    
    if not os.path.exists(backup_subdir):
        os.makedirs(backup_subdir)
    
    for file in LOCAL_FILES_TO_BACKUP:
        if os.path.exists(file):
            backup_file = os.path.join(backup_subdir, file)
            shutil.copy2(file, backup_file)
            logger.info(f"Backed up {file} to {backup_file}")
        else:
            logger.warning(f"File not found: {file}")
    
    return backup_subdir

def backup_to_cloud_storage(backup_dir):
    """Upload backups to Google Cloud Storage"""
    try:
        # Initialize GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET)
        
        # Upload each file in the backup directory
        for root, _, files in os.walk(backup_dir):
            for file in files:
                local_path = os.path.join(root, file)
                
                # Create GCS path
                rel_path = os.path.relpath(local_path, BACKUP_DIR)
                gcs_path = f"{GCS_BACKUP_PATH}/{rel_path}"
                
                # Upload file
                blob = bucket.blob(gcs_path)
                blob.upload_from_filename(local_path)
                logger.info(f"Uploaded {local_path} to gs://{GCS_BUCKET}/{gcs_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error uploading to Cloud Storage: {e}")
        return False

def cleanup_old_backups(max_backups=10):
    """Remove old backups to save space"""
    try:
        # List all backup directories
        backup_dirs = [os.path.join(BACKUP_DIR, d) for d in os.listdir(BACKUP_DIR) 
                      if os.path.isdir(os.path.join(BACKUP_DIR, d))]
        
        # Sort by creation time (oldest first)
        backup_dirs.sort(key=lambda x: os.path.getctime(x))
        
        # Remove old backups if we have more than max_backups
        if len(backup_dirs) > max_backups:
            dirs_to_remove = backup_dirs[:-max_backups]
            for dir_path in dirs_to_remove:
                shutil.rmtree(dir_path)
                logger.info(f"Removed old backup: {dir_path}")
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")

def main():
    """Main function to run backup process"""
    logger.info("Starting backup process...")
    
    # Ensure backup directory exists
    ensure_backup_dir()
    
    # Backup local files
    backup_dir = backup_local_files()
    logger.info(f"Local backup completed in {backup_dir}")
    
    # Upload to Cloud Storage
    cloud_result = backup_to_cloud_storage(backup_dir)
    if cloud_result:
        logger.info("Cloud Storage backup completed successfully")
    else:
        logger.warning("Cloud Storage backup failed")
    
    # Clean up old backups
    cleanup_old_backups()
    
    logger.info("Backup process completed")

if __name__ == "__main__":
    main()
