#!/usr/bin/env python3
"""
Enhanced script to restore a backup with detailed logging
"""
import sys
import os
import sqlite3
import json
from app import create_app, db

def detailed_restore(backup_name):
    app = create_app()
    with app.app_context():
        backup_path = os.path.join("instance/backups", backup_name)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup not found: {backup_path}")
            return False
            
        print(f"📂 Restoring backup from: {backup_path}")
        
        # Read metadata
        metadata_path = os.path.join(backup_path, "metadata.json")
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        print(f"📋 Backup metadata:")
        print(f"   User ID: {metadata.get('user_id')}")
        print(f"   Timestamp: {metadata.get('datetime')}")
        print(f"   Records: {metadata.get('database_records', {}).get('total_records', 0)}")
        
        # Check current database state
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"\n📊 Current database state:")
        tables = ["users", "family_members", "current_medications"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} records")
            except:
                print(f"   {table}: table not found")
        
        # Show backup data
        data_path = os.path.join(backup_path, "data")
        print(f"\n📦 Backup data:")
        for file in os.listdir(data_path):
            if file.endswith('.json'):
                file_path = os.path.join(data_path, file)
                with open(file_path) as f:
                    data = json.load(f)
                print(f"   {file}: {len(data)} records")
        
        conn.close()
        
        # Now try restore with backup manager
        from app.utils.backup_manager import BackupManager
        backup_manager = BackupManager()
        result = backup_manager.restore_backup(backup_path, user_id=None)
        
        print(f"\n🔄 Restore result:")
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   Database records: {result.get('database_restore', {}).get('total_restored', 0)}")
            print(f"   Files: {result.get('file_restore', {}).get('restored_files', 0)}")
            detailed_counts = result.get('database_restore', {}).get('restored_counts', {})
            for table, count in detailed_counts.items():
                if count > 0:
                    print(f"     {table}: {count}")
        else:
            print(f"   Error: {result.get('message', 'Unknown error')}")
        
        return result['status'] == 'success'

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python detailed_restore.py backup_directory_name")
        sys.exit(1)
    
    backup_name = sys.argv[1]
    success = detailed_restore(backup_name)
    sys.exit(0 if success else 1)
