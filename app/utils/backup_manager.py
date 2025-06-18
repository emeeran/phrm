"""
BackupManager utility for creating local backups of user data.
"""

import json
import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import current_app


class BackupManager:
    """Utility for managing backups of user data"""

    def __init__(self, backup_dir: Optional[str] = None):
        """Initialize the backup manager with an optional custom backup directory"""
        self.backup_dir = backup_dir or os.path.join(
            current_app.instance_path, "backups"
        )
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, user_id: int, include_files: bool = True) -> str:
        """
        Create a backup of all user data

        Args:
            user_id: The ID of the user to backup data for
            include_files: Whether to include uploaded files in the backup

        Returns:
            The path to the backup directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = str(uuid.uuid4())[:8]
        backup_name = f"backup_{user_id}_{timestamp}_{backup_id}"

        # Create backup directory
        backup_path = os.path.join(self.backup_dir, backup_name)
        os.makedirs(backup_path, exist_ok=True)

        # Backup database records
        db_backup = self._backup_user_data(user_id, backup_path)

        # Backup files if requested
        if include_files:
            file_backup = self._backup_user_files(user_id, backup_path)
        else:
            file_backup = {"status": "skipped", "files_count": 0}

        # Create metadata file
        metadata = {
            "backup_id": backup_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "include_files": include_files,
            "database_records": db_backup,
            "file_backup": file_backup,
        }

        with open(os.path.join(backup_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        return backup_path

    def list_backups(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        List all available backups

        Args:
            user_id: Optional filter to only show backups for a specific user

        Returns:
            List of backup metadata
        """
        backups = []

        # Iterate through backup directories
        for item in os.listdir(self.backup_dir):
            metadata_path = os.path.join(self.backup_dir, item, "metadata.json")

            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path) as f:
                        metadata = json.load(f)

                    # Filter by user_id if specified
                    if user_id is None or metadata.get("user_id") == user_id:
                        metadata["path"] = os.path.join(self.backup_dir, item)
                        backups.append(metadata)
                except:
                    # Skip invalid metadata files
                    continue

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return backups

    def restore_backup(self, backup_path: str, user_id: Optional[int] = None) -> Dict:
        """
        Restore a backup

        Args:
            backup_path: Path to the backup directory
            user_id: Optional user ID to verify ownership

        Returns:
            Status of the restore operation
        """
        # Verify backup exists and load metadata
        metadata_path = os.path.join(backup_path, "metadata.json")
        if not os.path.exists(metadata_path):
            return {
                "status": "error",
                "message": "Invalid backup path, metadata not found",
            }

        with open(metadata_path) as f:
            metadata = json.load(f)

        # Verify user ownership if a user_id was provided
        if user_id is not None and metadata.get("user_id") != user_id:
            return {
                "status": "error",
                "message": "Unauthorized: User ID does not match backup owner",
            }

        # Restore database records
        db_result = self._restore_database(backup_path, metadata)

        # Restore files if they were included in the backup
        if metadata.get("include_files", False):
            file_result = self._restore_files(backup_path, metadata)
        else:
            file_result = {
                "status": "skipped",
                "message": "Files were not included in this backup",
            }

        return {
            "status": "success" if db_result["status"] == "success" else "partial",
            "database_restore": db_result,
            "file_restore": file_result,
            "timestamp": datetime.now().isoformat(),
        }

    def delete_backup(self, backup_path: str, user_id: Optional[int] = None) -> Dict:
        """
        Delete a backup

        Args:
            backup_path: Path to the backup directory
            user_id: Optional user ID to verify ownership

        Returns:
            Status of the delete operation
        """
        # Verify backup exists and load metadata
        metadata_path = os.path.join(backup_path, "metadata.json")
        if not os.path.exists(metadata_path):
            return {
                "status": "error",
                "message": "Invalid backup path, metadata not found",
            }

        with open(metadata_path) as f:
            metadata = json.load(f)

        # Verify user ownership if a user_id was provided
        if user_id is not None and metadata.get("user_id") != user_id:
            return {
                "status": "error",
                "message": "Unauthorized: User ID does not match backup owner",
            }

        # Delete the backup directory
        try:
            shutil.rmtree(backup_path)
            return {
                "status": "success",
                "message": f"Backup deleted: {os.path.basename(backup_path)}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete backup: {e!s}"}

    def _backup_user_data(self, user_id: int, backup_path: str) -> Dict:
        """Backup all database records for a user to JSON files"""
        db_path = current_app.config["SQLALCHEMY_DATABASE_URI"].replace(
            "sqlite:///", ""
        )

        if not os.path.exists(db_path):
            return {"status": "error", "message": f"Database not found: {db_path}"}

        # Create data directory
        data_path = os.path.join(backup_path, "data")
        os.makedirs(data_path, exist_ok=True)

        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Track counts of backed up records
        record_counts = {}

        # Tables and their user ID columns for different relationships
        tables = {
            "users": {"id_column": "id", "filter_value": user_id},
            "family_members": {
                "id_column": "id",
                "records": self._get_user_family_members(cursor, user_id),
            },
            "health_records": {"id_column": "user_id", "filter_value": user_id},
            "medical_conditions": {"id_column": "user_id", "filter_value": user_id},
            "current_medications": {
                "id_column": "family_member_id",
                "parent_table": "family_members",
            },
            "documents": {
                "id_column": "health_record_id",
                "parent_table": "health_records",
            },
            "appointments": {"id_column": "user_id", "filter_value": user_id},
            "chat_messages": {"id_column": "user_id", "filter_value": user_id},
        }

        # Backup each table
        for table_name, config in tables.items():
            results = self._backup_table(cursor, table_name, config, data_path, user_id)
            record_counts[table_name] = results["count"]

        conn.close()

        return {
            "status": "success",
            "record_counts": record_counts,
            "total_records": sum(record_counts.values()),
        }

    def _backup_table(
        self, cursor, table_name: str, config: Dict, data_path: str, user_id: int
    ) -> Dict:
        """Backup a single table's data to a JSON file"""
        records = []

        try:
            # Direct filtering by user ID
            if "filter_value" in config:
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE {config['id_column']} = ?",
                    (config["filter_value"],),
                )
                records = [dict(row) for row in cursor.fetchall()]

            # Filtering by list of IDs from parent table
            elif "records" in config:
                ids = [record["id"] for record in config["records"]]
                if ids:
                    placeholders = ", ".join(["?"] * len(ids))
                    cursor.execute(
                        f"SELECT * FROM {table_name} WHERE {config['id_column']} IN ({placeholders})",
                        ids,
                    )
                    records = [dict(row) for row in cursor.fetchall()]

            # Filtering by foreign key in parent table
            elif "parent_table" in config:
                parent_ids = []

                # Get parent table records first
                if config["parent_table"] == "family_members":
                    parent_records = self._get_user_family_members(cursor, user_id)
                    parent_ids = [record["id"] for record in parent_records]
                elif config["parent_table"] == "health_records":
                    cursor.execute(
                        "SELECT id FROM health_records WHERE user_id = ?", (user_id,)
                    )
                    parent_ids = [row[0] for row in cursor.fetchall()]

                # Then get records from the target table
                if parent_ids:
                    placeholders = ", ".join(["?"] * len(parent_ids))
                    cursor.execute(
                        f"SELECT * FROM {table_name} WHERE {config['id_column']} IN ({placeholders})",
                        parent_ids,
                    )
                    records = [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            # Table might not exist or other database error
            return {"status": "error", "count": 0, "message": str(e)}

        # Save records to file
        if records:
            output_path = os.path.join(data_path, f"{table_name}.json")
            with open(output_path, "w") as f:
                json.dump(records, f, indent=2)

        return {"status": "success", "count": len(records)}

    def _get_user_family_members(self, cursor, user_id: int) -> List[Dict]:
        """Get all family members associated with a user through the user_family association table"""
        try:
            cursor.execute(
                """
                SELECT fm.* FROM family_members fm
                JOIN user_family uf ON fm.id = uf.family_member_id
                WHERE uf.user_id = ?
            """,
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            # Table might not exist or other error
            return []

    def _backup_user_files(self, user_id: int, backup_path: str) -> Dict:
        """Backup all files associated with a user and their family members"""
        files_path = os.path.join(backup_path, "files")
        os.makedirs(files_path, exist_ok=True)

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        user_upload_dir = os.path.join(upload_dir, str(user_id))

        copied_files = 0

        # Copy user's upload directory if it exists
        if os.path.exists(user_upload_dir):
            user_files_path = os.path.join(files_path, str(user_id))
            shutil.copytree(user_upload_dir, user_files_path)

            # Count files
            for _, _, filenames in os.walk(user_files_path):
                copied_files += len(filenames)

        return {
            "status": "success" if copied_files > 0 else "no_files",
            "files_count": copied_files,
        }

    def _restore_database(self, backup_path: str, metadata: Dict) -> Dict:
        """Restore database records from a backup"""
        data_path = os.path.join(backup_path, "data")
        if not os.path.exists(data_path):
            return {"status": "error", "message": "No data directory found in backup"}

        # Connect to database
        db_path = current_app.config["SQLALCHEMY_DATABASE_URI"].replace(
            "sqlite:///", ""
        )
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Track restored record counts
        restored_counts = {}

        # Order matters for foreign key constraints
        # We'll restore in specific order to maintain data integrity
        restore_order = [
            "users",
            "family_members",
            "user_family",
            "medical_conditions",
            "current_medications",
            "health_records",
            "documents",
            "appointments",
            "chat_messages",
        ]

        # Restore each table in order
        for table_name in restore_order:
            table_path = os.path.join(data_path, f"{table_name}.json")
            if not os.path.exists(table_path):
                restored_counts[table_name] = 0
                continue

            with open(table_path) as f:
                records = json.load(f)

            if records:
                count = self._restore_table(cursor, table_name, records)
                restored_counts[table_name] = count
            else:
                restored_counts[table_name] = 0

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "restored_counts": restored_counts,
            "total_restored": sum(restored_counts.values()),
        }

    def _restore_table(self, cursor, table_name: str, records: List[Dict]) -> int:
        """Restore records to a table, handling duplicates appropriately"""
        restored_count = 0

        for record in records:
            # Get column names and values
            columns = list(record.keys())
            values = [record[col] for col in columns]

            # SQL for checking if record exists
            id_check_sql = f"SELECT COUNT(*) FROM {table_name} WHERE id = ?"

            try:
                # Check if record with this ID already exists
                cursor.execute(id_check_sql, (record["id"],))
                exists = cursor.fetchone()[0] > 0

                if exists:
                    # Skip or update existing record
                    continue
                else:
                    # Insert new record
                    placeholders = ", ".join(["?"] * len(values))
                    columns_str = ", ".join(columns)
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    cursor.execute(sql, values)
                    restored_count += 1

            except sqlite3.Error:
                # Continue with next record on error
                continue

        return restored_count

    def _restore_files(self, backup_path: str, metadata: Dict) -> Dict:
        """Restore files from a backup"""
        files_path = os.path.join(backup_path, "files")
        if not os.path.exists(files_path):
            return {"status": "error", "message": "No files directory found in backup"}

        upload_dir = current_app.config["UPLOAD_FOLDER"]

        restored_files = 0

        # Iterate through user directories in the backup
        for item in os.listdir(files_path):
            source_dir = os.path.join(files_path, item)
            if os.path.isdir(source_dir):
                # Create destination directory
                dest_dir = os.path.join(upload_dir, item)
                os.makedirs(dest_dir, exist_ok=True)

                # Copy files, carefully merging with existing files
                for root, _, files in os.walk(source_dir):
                    rel_path = os.path.relpath(root, source_dir)
                    dest_path = os.path.join(dest_dir, rel_path)
                    os.makedirs(dest_path, exist_ok=True)

                    for filename in files:
                        source_file = os.path.join(root, filename)
                        dest_file = os.path.join(dest_path, filename)

                        # Only copy if file doesn't exist or is different
                        if not os.path.exists(
                            dest_file
                        ) or not self._files_are_identical(source_file, dest_file):
                            shutil.copy2(source_file, dest_file)
                            restored_files += 1

        return {
            "status": "success" if restored_files > 0 else "no_files",
            "restored_files": restored_files,
        }

    def _files_are_identical(self, file1: str, file2: str) -> bool:
        """Check if two files have identical content"""
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False

        # Compare file contents
        with open(file1, "rb") as f1, open(file2, "rb") as f2:
            chunk_size = 8192  # 8KB chunks
            while True:
                chunk1 = f1.read(chunk_size)
                chunk2 = f2.read(chunk_size)

                if chunk1 != chunk2:
                    return False

                if not chunk1:  # End of file
                    break

        return True
