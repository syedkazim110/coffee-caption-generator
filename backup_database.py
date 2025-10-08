#!/usr/bin/env python3
"""
Database Backup Script
Creates a backup of the PostgreSQL database before cleaning operations
"""

import subprocess
import datetime
import os
import sys

def create_backup():
    """Create a PostgreSQL database backup"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"reddit_db_backup_{timestamp}.sql"
    
    # Database connection parameters
    db_host = "localhost"
    db_port = "5434"
    db_name = "reddit_db"
    db_user = "postgres"
    
    print(f"Creating backup: {backup_filename}")
    
    try:
        # Create backup using pg_dump
        cmd = [
            "pg_dump",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-f", backup_filename,
            "--verbose",
            "--no-password"
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = "password"
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup created successfully: {backup_filename}")
            print(f"Backup size: {os.path.getsize(backup_filename)} bytes")
            return backup_filename
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return None

def restore_backup(backup_file):
    """Restore database from backup file"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Database connection parameters
    db_host = "localhost"
    db_port = "5434"
    db_name = "reddit_db"
    db_user = "postgres"
    
    print(f"Restoring from backup: {backup_file}")
    
    try:
        # Restore using psql
        cmd = [
            "psql",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-f", backup_file,
            "--quiet"
        ]
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = "password"
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database restored successfully from {backup_file}")
            return True
        else:
            print(f"❌ Restore failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error restoring backup: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Usage: python backup_database.py restore <backup_file>")
    else:
        create_backup()
