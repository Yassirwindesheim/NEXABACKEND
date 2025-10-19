from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # <-- IMPORT selectinload

from app.db import get_session
from app.models import Workorder, Task # Task is only needed for the calculation logic
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/portal", tags=["portal"])

# (PortalTask and PortalWO classes remain the same)
class PortalTask(BaseModel):
    name: str
    status: str

class PortalWO(BaseModel):
    id: str
    vehicle: str
    customer: str
    complaint: Optional[str] = None
    status: str
    progress_pct: int
    tasks: list[PortalTask]
# ----------------------------------------------------------------------

@router.get("/{workorder_id}", response_model=PortalWO)
async def portal_workorder(workorder_id: str, db: AsyncSession = Depends(get_session)):
    
    # 1. Eager-Load Customer and Tasks to prevent MissingGreenlet error
    q = (
        select(Workorder)
        .where(Workorder.id == workorder_id)
        .options(
            selectinload(Workorder.customer), # Load the related Customer data now
            selectinload(Workorder.tasks)     # Load the related Tasks data now
        )
    )
    
    # Execute the single, optimized query
    w = (await db.execute(q)).scalar_one_or_none()
    
    if not w:
        raise HTTPException(404, "Not found")

    # The tasks are now available directly and non-blockingly
    ts = w.tasks
    
    # 2. Calculate Progress
    total = max(1, len(ts))
    done = len([t for t in ts if t.status == "Afgerond"]) 
    progress = round(done / total * 100)
    
    # 3. Return the result
    return PortalWO(
        id=w.id, 
        vehicle=w.vehicle, 
        # FIX: Access the customer's name attribute for the PortalWO string field
        customer=w.customer.name, 
        complaint=w.complaint,
        status=w.status, 
        progress_pct=progress,
        tasks=[PortalTask(name=t.name, status=t.status) for t in ts]
    )