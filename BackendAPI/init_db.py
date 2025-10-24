#!/usr/bin/env python3
"""
Database initialization script.

This script creates the database tables and sets up initial data
including default roles. Authentication is disabled.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import create_tables, init_db, get_db_context
from src.database.models import User, Role, UserRole, UserRoleEnum

def create_admin_user():
    """Create default system user if it doesn't exist."""
    
    with get_db_context() as db:
        # Check if system user already exists
        existing_user = db.query(User).filter(User.username == "system").first()
        if existing_user:
            print("System user 'system' already exists")
            return
        
        # Create system user with dummy password
        system_user = User(
            username="system",
            email="system@testmanager.com",
            hashed_password="no-auth-required",
            is_active=True
        )
        db.add(system_user)
        db.flush()
        
        # Get admin role
        admin_role = db.query(Role).filter(Role.name == UserRoleEnum.ADMIN).first()
        if admin_role:
            # Assign admin role to user
            user_role = UserRole(
                user_id=system_user.id,
                role_id=admin_role.id
            )
            db.add(user_role)
        
        db.commit()
        print("Created system user (authentication disabled)")

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
        
        # Create system user
        print("Creating system user...")
        create_admin_user()
        
        print("Database initialization completed successfully!")
        print("Note: Authentication is disabled - all endpoints are public")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
