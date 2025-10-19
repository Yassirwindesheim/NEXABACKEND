# app/scripts/create_admin.py
"""
Admin user creation script.
Usage: python -m app.scripts.create_admin

Best practices:
1. Never commit admin credentials to git
2. Use environment variables for sensitive data
3. Run once during initial setup
4. Keep script for future admin creation needs
"""
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import Employee, RoleEnum
from app.deps import hash_password

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

async def create_admin_user(email: str, password: str, name: str):
    """Creates or updates an employee to be an Admin"""
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(
            select(Employee).where(Employee.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"⚠️  User {email} already exists.")
            response = input("Update to Admin role? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
            
            existing_user.role = RoleEnum.Admin
            existing_user.password_hash = hash_password(password)
            existing_user.is_active = True
            print(f"✅ Updated {email} to Admin role")
        else:
            print(f"Creating new admin user: {email}")
            new_admin = Employee(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=RoleEnum.Admin,
                is_active=True
            )
            session.add(new_admin)
            print(f"✅ Created admin user: {email}")
        
        await session.commit()
        print(f"\n📋 Admin Credentials:")
        print(f"   Email: {email}")
        print(f"   Role: Admin")
        print(f"\n⚠️  Store the password securely!")

async def main():
    """Interactive prompt for admin creation"""
    print("=" * 50)
    print("🔐 Admin User Creation Script")
    print("=" * 50)
    
    # Get admin details from user input
    email = input("\nAdmin Email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return
    
    name = input("Admin Name: ").strip()
    if not name:
        print("❌ Name cannot be empty")
        return
    
    password = input("Admin Password: ").strip()
    if not password or len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return
    
    confirm_password = input("Confirm Password: ").strip()
    if password != confirm_password:
        print("❌ Passwords do not match")
        return
    
    print(f"\n📝 Creating admin user with:")
    print(f"   Email: {email}")
    print(f"   Name: {name}")
    response = input("\nProceed? (y/n): ")
    
    if response.lower() == 'y':
        await create_admin_user(email, password, name)
    else:
        print("Cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)