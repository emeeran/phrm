#!/usr/bin/env python3
"""
Force restore script that can overwrite existing records or create new ones
"""
import sys
import os
import sqlite3
import json
from datetime import datetime
from app import create_app, db

def force_restore_backup(backup_name, mode='overwrite'):
    """
    Force restore a backup with options:
    - overwrite: Replace existing records with same IDs
    - new_ids: Create new records with new IDs
    """
    app = create_app()
    with app.app_context():
        backup_path = os.path.join("instance/backups", backup_name)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup not found: {backup_path}")
            return False
            
        print(f"🔄 Force restoring backup: {backup_name}")
        print(f"📋 Mode: {mode}")
        
        # Read metadata
        metadata_path = os.path.join(backup_path, "metadata.json")
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        # Connect to database
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        data_path = os.path.join(backup_path, "data")
        restored_total = 0
        
        # Restore order matters for foreign keys
        restore_order = [
            "users",
            "family_members", 
            "current_medications",
            "health_records",
            "documents",
            "appointments",
            "chat_messages",
        ]
        
        for table_name in restore_order:
            table_path = os.path.join(data_path, f"{table_name}.json")
            if not os.path.exists(table_path):
                continue
                
            with open(table_path) as f:
                records = json.load(f)
            
            if not records:
                continue
                
            print(f"\n📊 Processing {table_name}: {len(records)} records")
            
            count = 0
            for record in records:
                try:
                    columns = list(record.keys())
                    values = [record[col] for col in columns]
                    
                    if mode == 'overwrite':
                        # Delete existing record with same ID, then insert
                        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record["id"],))
                        
                        # Insert the record
                        placeholders = ", ".join(["?"] * len(values))
                        columns_str = ", ".join(columns)
                        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                        count += 1
                        
                    elif mode == 'new_ids':
                        # Get the next available ID
                        cursor.execute(f"SELECT MAX(id) FROM {table_name}")
                        result = cursor.fetchone()
                        next_id = (result[0] if result[0] else 0) + 1
                        
                        # Update the record with new ID
                        record["id"] = next_id
                        values = [record[col] for col in columns]
                        
                        # Insert with new ID
                        placeholders = ", ".join(["?"] * len(values))
                        columns_str = ", ".join(columns)
                        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                        count += 1
                        
                except sqlite3.Error as e:
                    print(f"   ⚠️  Error with record ID {record.get('id', 'unknown')}: {e}")
                    continue
            
            print(f"   ✅ Restored {count} records")
            restored_total += count
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Force restore completed!")
        print(f"   Total records restored: {restored_total}")
        
        # Also restore files if they exist
        files_path = os.path.join(backup_path, "files")
        if os.path.exists(files_path):
            print(f"\n📁 Restoring files...")
            upload_dir = app.config["UPLOAD_FOLDER"]
            
            restored_files = 0
            for item in os.listdir(files_path):
                source_dir = os.path.join(files_path, item)
                if os.path.isdir(source_dir):
                    dest_dir = os.path.join(upload_dir, item)
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    for file in os.listdir(source_dir):
                        source_file = os.path.join(source_dir, file)
                        dest_file = os.path.join(dest_dir, file)
                        
                        if not os.path.exists(dest_file):
                            import shutil
                            shutil.copy2(source_file, dest_file)
                            restored_files += 1
            
            print(f"   Files restored: {restored_files}")
        
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python force_restore.py backup_directory_name [mode]")
        print("Modes:")
        print("  overwrite (default) - Replace existing records with same IDs")
        print("  new_ids            - Create new records with new IDs")
        sys.exit(1)
    
    backup_name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) == 3 else 'overwrite'
    
    if mode not in ['overwrite', 'new_ids']:
        print("❌ Invalid mode. Use 'overwrite' or 'new_ids'")
        sys.exit(1)
    
    success = force_restore_backup(backup_name, mode)
    sys.exit(0 if success else 1)
