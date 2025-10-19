import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
# --- NEW IMPORTS (Using standalone bcrypt) ---
import bcrypt
# Removed: from passlib.context import CryptContext
# ---------------------------------------------

from app.db import get_session
from app.models import Employee

SECRET_KEY = (os.getenv("SECRET_KEY") or "change-me-in-.env").strip()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
bearer_scheme = HTTPBearer(auto_error=False)

# --- NEW HASHING FUNCTIONS ---
def hash_password(password: str) -> str:
    """Hashes the plain password using bcrypt."""
    # bcrypt requires bytes for hashing
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # Decode back to string for database storage
    return hashed_bytes.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verifies the plain password against the stored hash."""
    # Both inputs must be encoded to bytes for bcrypt.checkpw
    plain_bytes = plain.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)
# -----------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthedUser(BaseModel):
    user_id: int
    email: str
    role: Optional[str] = None

def create_access_token(data: dict, minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=minutes)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_employee_by_email(db: AsyncSession, email: str) -> Optional[Employee]:
    res = await db.execute(select(Employee).where(Employee.email == email))
    return res.scalar_one_or_none()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_session),
) -> AuthedUser:
    if not creds or creds.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Missing token",
                            headers={"WWW-Authenticate": "Bearer"})
    token = creds.credentials.strip()
    
    try:
        # 🌟 FIX: Wrap the synchronous jwt.decode call 🌟
        # Use asyncio.to_thread to run the blocking code in a separate thread.
        payload = await asyncio.to_thread(
            jwt.decode, 
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    sub = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role")
    if not sub or not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # optional: ensure the employee still exists & is active
    emp = await get_employee_by_email(db, email)
    if not emp or emp.id != int(sub) or emp.is_active is False:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return AuthedUser(user_id=emp.id, email=emp.email, role=role)


async def require_admin(user: AuthedUser = Depends(get_current_user)) -> AuthedUser:
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user
