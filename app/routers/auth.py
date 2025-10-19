from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from app.db import get_session
from app.models import Employee, RoleEnum
# UPDATED IMPORTS: Removed pwd_context, added hash_password
from app.deps import create_access_token, verify_password, hash_password, Token, AuthedUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------- New: JSON body for registration ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: constr(min_length=8) # type: ignore
    name: constr(min_length=1) # type: ignore
    role: RoleEnum = RoleEnum.Monteur    # default

@router.post("/register", response_model=Token)
async def register_user(payload: RegisterIn, db: AsyncSession = Depends(get_session)):
    # 1) ensure email is unique
    existing = await db.execute(select(Employee.id).where(Employee.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2) hash the password
    # CHANGED: Now calling the new hash_password function from app.deps
    hashed = hash_password(payload.password)

    # 3) insert (pass RoleEnum, not str)
    stmt = (
        insert(Employee)
        .values(
            name=payload.name,
            email=payload.email,
            role=payload.role,              # Enum value goes in
            password_hash=hashed,
            is_active=True,
        )
        .returning(Employee.id)
    )
    emp_id = (await db.execute(stmt)).scalar_one()
    await db.commit()

    # 4) create JWT
    token = create_access_token({"sub": str(emp_id), "email": payload.email, "role": payload.role.value})
    return {"access_token": token, "token_type": "bearer"}

# ---------- login/me unchanged ----------
@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    res = await db.execute(select(Employee).where(Employee.email == form.username))
    emp = res.scalar_one_or_none()

    if not emp or not emp.password_hash or not verify_password(form.password, emp.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    token = create_access_token({"sub": str(emp.id), "email": emp.email, "role": emp.role.value})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=AuthedUser)
async def me(current: AuthedUser = Depends(get_current_user)):
    return current
