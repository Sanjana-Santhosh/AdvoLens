#!/usr/bin/env python3
"""
Seed script for AdvoLens - Run inside Docker container or locally
Creates admin users, department emails, and sample data

Usage:
  Local:  python -m app.scripts.seed_data
  Docker: docker exec -it advolens-backend python -m app.scripts.seed_data
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User, Department
from app.models.issue import Issue
from app.core.security import get_password_hash
from geoalchemy2.elements import WKTElement


def seed_admin_users(db: Session):
    """Create default admin users for each department"""
    
    admins = [
        {
            "email": "admin@advolens.com",
            "password": "admin123",  # Change in production!
            "full_name": "Super Admin",
            "department": Department.OTHER,
            "is_superuser": True,
        },
        {
            "email": "municipality@advolens.com",
            "password": "muni123",
            "full_name": "Municipality Admin",
            "department": Department.MUNICIPALITY,
            "is_superuser": False,
        },
        {
            "email": "pwd@advolens.com",
            "password": "pwd123",
            "full_name": "PWD Admin",
            "department": Department.PWD,
            "is_superuser": False,
        },
        {
            "email": "kseb@advolens.com",
            "password": "kseb123",
            "full_name": "KSEB Admin",
            "department": Department.KSEB,
            "is_superuser": False,
        },
        {
            "email": "water@advolens.com",
            "password": "water123",
            "full_name": "Water Authority Admin",
            "department": Department.WATER_AUTHORITY,
            "is_superuser": False,
        },
    ]
    
    created = 0
    for admin_data in admins:
        # Check if user already exists
        existing = db.query(User).filter(User.email == admin_data["email"]).first()
        if existing:
            print(f"  ⏭️  User {admin_data['email']} already exists, skipping...")
            continue
        
        user = User(
            email=admin_data["email"],
            hashed_password=get_password_hash(admin_data["password"]),
            full_name=admin_data["full_name"],
            department=admin_data["department"],
            is_active=True,
            is_superuser=admin_data.get("is_superuser", False),
        )
        db.add(user)
        created += 1
        print(f"  ✅ Created user: {admin_data['email']}")
    
    db.commit()
    return created


def seed_sample_issues(db: Session):
    """Create sample issues for testing"""
    
    sample_issues = [
        {
            "title": "Garbage pile on MG Road",
            "description": "Large garbage pile near bus stop",
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "status": "Open",
            "caption": "Overflowing garbage bin with plastic waste on main road",
            "tags": ["municipality", "garbage", "street_litter", "plastic_waste"],
            "department": Department.MUNICIPALITY,
            "lat": 8.5241,
            "lon": 76.9366,
            "citizen_token": "demo_token_1",
        },
        {
            "title": "Pothole on Highway",
            "description": "Deep pothole causing accidents",
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "status": "In Progress",
            "caption": "Large pothole on national highway near junction",
            "tags": ["pwd", "pothole", "road_damage", "road"],
            "department": Department.PWD,
            "lat": 8.5300,
            "lon": 76.9400,
            "citizen_token": "demo_token_2",
        },
        {
            "title": "Broken Streetlight",
            "description": "Streetlight not working for 2 weeks",
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "status": "Open",
            "caption": "Non-functional streetlight creating safety hazard at night",
            "tags": ["kseb", "streetlight", "electrical", "pole"],
            "department": Department.KSEB,
            "lat": 8.5180,
            "lon": 76.9300,
            "citizen_token": "demo_token_3",
        },
        {
            "title": "Water Pipeline Leak",
            "description": "Major water leak wasting water",
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "status": "Resolved",
            "caption": "Burst water pipeline flooding the street",
            "tags": ["water_authority", "water", "leak", "pipe"],
            "department": Department.WATER_AUTHORITY,
            "lat": 8.5100,
            "lon": 76.9450,
            "citizen_token": "demo_token_4",
        },
    ]
    
    # Check if we already have issues
    existing_count = db.query(Issue).count()
    if existing_count > 0:
        print(f"  ⏭️  {existing_count} issues already exist, skipping sample data...")
        return 0
    
    created = 0
    for issue_data in sample_issues:
        location_wkt = f"POINT({issue_data['lon']} {issue_data['lat']})"
        
        issue = Issue(
            title=issue_data["title"],
            description=issue_data["description"],
            image_url=issue_data["image_url"],
            status=issue_data["status"],
            caption=issue_data["caption"],
            tags=issue_data["tags"],
            department=issue_data["department"],
            location=WKTElement(location_wkt, srid=4326),
            citizen_token=issue_data["citizen_token"],
            upvote_count=0,
            priority_score=0,
        )
        db.add(issue)
        created += 1
        print(f"  ✅ Created issue: {issue_data['title']}")
    
    db.commit()
    return created


def main():
    print("\n" + "="*50)
    print("🌱 AdvoLens Database Seeder")
    print("="*50 + "\n")
    
    db = SessionLocal()
    
    try:
        # Seed admin users
        print("👤 Creating admin users...")
        admin_count = seed_admin_users(db)
        print(f"   Created {admin_count} new admin users\n")
        
        # Seed sample issues (optional - only if no issues exist)
        print("📝 Creating sample issues...")
        issue_count = seed_sample_issues(db)
        print(f"   Created {issue_count} sample issues\n")
        
        print("="*50)
        print("✅ Seeding complete!")
        print("="*50)
        print("\n📋 Admin Credentials:")
        print("   Super Admin:  admin@advolens.com / admin123")
        print("   Municipality: municipality@advolens.com / muni123")
        print("   PWD:          pwd@advolens.com / pwd123")
        print("   KSEB:         kseb@advolens.com / kseb123")
        print("   Water:        water@advolens.com / water123")
        print("\n⚠️  Remember to change passwords in production!\n")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
