#!/usr/bin/env python3
"""
Comprehensive database path diagnostic and fix
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/home/em/code/wip/phrm')

def check_environment():
    """Check current environment and variables"""
    print("🔍 Environment Diagnostic")
    print("=" * 50)
    
    # Current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Check if .env file exists and load it
    env_file = '/home/em/code/wip/phrm/.env'
    print(f".env file exists: {os.path.exists(env_file)}")
    
    if os.path.exists(env_file):
        print("\n📋 .env file contents:")
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    print(f"  {line.strip()}")
    
    # Load environment variables from .env
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("\n✅ .env loaded successfully")
    except ImportError:
        print("\n⚠️ python-dotenv not available")
    
    # Check environment variables
    print(f"\nSQLALCHEMY_DATABASE_URI from env: {os.environ.get('SQLALCHEMY_DATABASE_URI', 'NOT SET')}")
    print(f"DATABASE_URL from env: {os.environ.get('DATABASE_URL', 'NOT SET')}")
    
    # Check app config
    try:
        from app.config import Config
        config = Config()
        print(f"\nApp config SQLALCHEMY_DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI}")
    except Exception as e:
        print(f"\n❌ Error loading app config: {e}")

def check_database_paths():
    """Check various potential database paths"""
    print("\n🗄️ Database Path Analysis")
    print("=" * 50)
    
    base_dir = '/home/em/code/wip/phrm'
    potential_paths = [
        f"{base_dir}/phrm.db",
        f"{base_dir}/instance/phrm.db",
        f"{os.getcwd()}/phrm.db",
        f"{os.getcwd()}/instance/phrm.db",
        "phrm.db",
        "instance/phrm.db"
    ]
    
    for path in potential_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(path)
        abs_exists = os.path.exists(abs_path)
        
        print(f"\nPath: {path}")
        print(f"  Absolute: {abs_path}")
        print(f"  Exists (relative): {exists}")
        print(f"  Exists (absolute): {abs_exists}")
        
        if exists or abs_exists:
            actual_path = path if exists else abs_path
            try:
                # Test SQLite connection
                conn = sqlite3.connect(actual_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                print(f"  ✅ SQLite accessible, tables: {len(tables)}")
            except Exception as e:
                print(f"  ❌ SQLite error: {e}")

def fix_database_path():
    """Fix the database path issue"""
    print("\n🔧 Fixing Database Path")
    print("=" * 50)
    
    # The correct absolute path
    correct_db_path = "/home/em/code/wip/phrm/instance/phrm.db"
    
    # Check if it exists
    if not os.path.exists(correct_db_path):
        print(f"❌ Database file not found at: {correct_db_path}")
        return False
    
    # Update .env file with absolute path
    env_file = '/home/em/code/wip/phrm/.env'
    
    # Read current .env
    lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    
    # Update or add the database URI
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('SQLALCHEMY_DATABASE_URI='):
            lines[i] = f"SQLALCHEMY_DATABASE_URI=sqlite:///{correct_db_path}\n"
            updated = True
            print(f"✅ Updated existing SQLALCHEMY_DATABASE_URI")
            break
    
    if not updated:
        lines.append(f"SQLALCHEMY_DATABASE_URI=sqlite:///{correct_db_path}\n")
        print(f"✅ Added SQLALCHEMY_DATABASE_URI")
    
    # Write back to .env
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ .env file updated with absolute database path")
    return True

def test_flask_db_connection():
    """Test Flask database connection"""
    print("\n🧪 Testing Flask Database Connection")
    print("=" * 50)
    
    try:
        os.chdir('/home/em/code/wip/phrm')
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Import Flask app components
        from app import create_app
        from app.models.core.user import User
        
        # Create app
        app = create_app()
        
        with app.app_context():
            print(f"App database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Test database connection
            try:
                users = User.query.limit(1).all()
                print(f"✅ Database connection successful, found {len(users)} user(s)")
                
                # Try to find demo user
                demo_user = User.query.filter_by(email='demo@example.com').first()
                if demo_user:
                    print(f"✅ Demo user found: {demo_user.email}")
                else:
                    print("⚠️ Demo user not found")
                
                return True
                
            except Exception as e:
                print(f"❌ Database query failed: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🏥 PHRM Database Diagnostic Tool")
    print("=" * 60)
    
    # Step 1: Check environment
    check_environment()
    
    # Step 2: Check database paths
    check_database_paths()
    
    # Step 3: Fix database path
    if fix_database_path():
        # Step 4: Test Flask connection
        success = test_flask_db_connection()
        
        if success:
            print("\n🎉 Database issue RESOLVED!")
            print("Restart the Flask app to apply changes.")
        else:
            print("\n💥 Database issue still exists.")
    else:
        print("\n💥 Could not fix database path.")
