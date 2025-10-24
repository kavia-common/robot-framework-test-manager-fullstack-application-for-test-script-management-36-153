#!/usr/bin/env python3
"""
Database initialization script.

This script creates the database tables and sets up initial data
including default roles and an admin user.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database.connection import create_tables, init_db, get_db_context
from src.database.models import User, Role, UserRole, UserRoleEnum
from src.auth.jwt_handler import get_password_hash

def create_admin_user():
    """Create default admin user if it doesn't exist."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@testmanager.com")
    
    with get_db_context() as db:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == admin_username).first()
        if existing_admin:
            print(f"Admin user '{admin_username}' already exists")
            return
        
        # Create admin user
        admin_user = User(
            username=admin_username,
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True
        )
        db.add(admin_user)
        db.flush()
        
        # Get admin role
        admin_role = db.query(Role).filter(Role.name == UserRoleEnum.ADMIN).first()
        if admin_role:
            # Assign admin role to user
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=admin_role.id
            )
            db.add(user_role)
        
        db.commit()
        print(f"Created admin user: {admin_username} with password: {admin_password}")
        print("Please change the default password after first login!")

def main():
    """Main initialization function."""
    print("Initializing Robot Framework Test Manager database...")
    
    # Load environment variables
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
    
    try:
        # Create tables
        print("Creating database tables...")
        create_tables()
        
        # Initialize with default data
        print("Setting up default roles...")
        init_db()
        
        # Create admin user
        print("Creating admin user...")
        create_admin_user()
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
