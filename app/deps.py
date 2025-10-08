import os
from fastapi import Header, HTTPException
from jose import jwt, JWTError
from pydantic import BaseModel

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
JWT_AUD = os.getenv("SUPABASE_JWT_AUD", "authenticated")

class AuthedUser(BaseModel):
    user_id: str
    org_id: str

async def get_current_user(
    authorization: str = Header(None),
    x_org_id: str = Header(None)
) -> AuthedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    if not JWT_SECRET:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        if not x_org_id:
            raise HTTPException(status_code=400, detail="Missing X-Org-Id header")
        return AuthedUser(user_id=sub, org_id=x_org_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")