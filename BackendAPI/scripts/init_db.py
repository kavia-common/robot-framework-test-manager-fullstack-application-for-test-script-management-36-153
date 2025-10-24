"""
Database initialization script.
Creates tables and seeds initial data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import init_db, get_db
from src.database.models import User, Role, UserRole, RoleEnum
from src.core.security import get_password_hash
from src.services.auth_service import auth_service


def create_default_admin():
    """Create default admin user if not exists"""
    db = next(get_db())
    
    # Check if admin exists
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        print("Admin user already exists")
        return
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        full_name="System Administrator",
        hashed_password=get_password_hash("admin123"),
        is_active=1
    )
    db.add(admin)
    db.flush()
    
    # Assign admin role
    admin_role = db.query(Role).filter(Role.name == RoleEnum.ADMIN).first()
    if admin_role:
        user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
        db.add(user_role)
    
    db.commit()
    print("Default admin user created:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  IMPORTANT: Change this password in production!")


def main():
    """Main initialization function"""
    print("Initializing database...")
    
    # Initialize database tables
    init_db()
    print("✓ Database tables created")
    
    # Initialize default roles
    db = next(get_db())
    auth_service.init_default_roles(db)
    print("✓ Default roles created")
    
    # Create default admin user
    create_default_admin()
    print("✓ Default admin user created")
    
    print("\nDatabase initialization complete!")
    print("\nYou can now start the application with:")
    print("  uvicorn src.api.main:app --reload")


if __name__ == "__main__":
    main()
