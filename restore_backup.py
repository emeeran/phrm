#!/usr/bin/env python3
"""
Script to restore a backup using the BackupManager
"""
import sys
import os
from app import create_app, db
from app.utils.backup_manager import BackupManager

def restore_backup_script(backup_name):
    app = create_app()
    with app.app_context():
        backup_manager = BackupManager()
        backup_path = os.path.join(backup_manager.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            print(f"Backup not found: {backup_path}")
            return False
            
        print(f"Restoring backup from: {backup_path}")
        
        # Use user_id=None to bypass user verification (admin restore)
        result = backup_manager.restore_backup(backup_path, user_id=None)
        
        if result['status'] == 'success':
            print("✅ Backup restored successfully!")
            print(f"Database records restored: {result.get('database_restore', {}).get('total_restored', 0)}")
            print(f"Files restored: {result.get('file_restore', {}).get('restored_files', 0)}")
            return True
        else:
            print(f"❌ Restore failed: {result.get('message', 'Unknown error')}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_backup.py backup_directory_name")
        sys.exit(1)
    
    backup_name = sys.argv[1]
    success = restore_backup_script(backup_name)
    sys.exit(0 if success else 1)
