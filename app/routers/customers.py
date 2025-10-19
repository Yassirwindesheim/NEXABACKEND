# app/routers/customers.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db import get_session 
from app.models import Customer # Assuming this SQLAlchemy model exists
from app.schemas import CustomerOut 
from app.deps import get_current_user, AuthedUser 

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("", response_model=List[CustomerOut])
async def list_customers(
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Fetches a list of all customers, ordered by name, for use in the work order form.
    """
    # Select all customers and order them alphabetically by name
    q = select(Customer).order_by(Customer.name)
    
    res = await db.execute(q)
    
    return res.scalars().all()