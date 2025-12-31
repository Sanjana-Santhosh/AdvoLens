"""
Script to create an initial super admin user.
Run this after running the database migrations.

Usage:
    python -m app.scripts.create_admin
"""
import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.auth import get_password_hash
from app.models.user import User, UserRole, Department


def create_super_admin(
    email: str = "admin@advolens.gov",
    password: str = "admin123",  # Change this in production!
    name: str = "Super Admin"
):
    """Create a super admin user if one doesn't exist."""
    db: Session = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists.")
            return
        
        # Create super admin
        admin_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            name=name,
            role=UserRole.SUPER_ADMIN,
            department=None  # Super admins don't belong to a specific department
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Super Admin created successfully!")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"   ⚠️  Remember to change the password in production!")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()


def create_department_officials():
    """Create sample department officials for testing."""
    db: Session = SessionLocal()
    
    officials = [
        {"email": "municipality@advolens.gov", "name": "Municipal Officer", "dept": Department.MUNICIPALITY},
        {"email": "water@advolens.gov", "name": "Water Authority Officer", "dept": Department.WATER_AUTHORITY},
        {"email": "kseb@advolens.gov", "name": "KSEB Officer", "dept": Department.KSEB},
        {"email": "pwd@advolens.gov", "name": "PWD Officer", "dept": Department.PWD},
    ]
    
    try:
        for official in officials:
            existing = db.query(User).filter(User.email == official["email"]).first()
            if existing:
                print(f"User {official['email']} already exists, skipping...")
                continue
            
            user = User(
                email=official["email"],
                hashed_password=get_password_hash("official123"),
                name=official["name"],
                role=UserRole.OFFICIAL,
                department=official["dept"]
            )
            db.add(user)
        
        db.commit()
        print(f"✅ Department officials created successfully!")
        print(f"   Default password: official123")
        
    except Exception as e:
        print(f"❌ Error creating officials: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating initial users...")
    print("-" * 40)
    create_super_admin()
    print("-" * 40)
    create_department_officials()
    print("-" * 40)
    print("Done!")
