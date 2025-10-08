from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Workorder, Task
from pydantic import BaseModel

router = APIRouter(prefix="/portal", tags=["portal"])

class PortalTask(BaseModel):
    name: str
    status: str

class PortalWO(BaseModel):
    id: str
    vehicle: str
    customer: str
    complaint: str | None
    status: str
    progress_pct: int
    tasks: list[PortalTask]

@router.get("/{workorder_id}", response_model=PortalWO)
async def portal_workorder(workorder_id: str, db: AsyncSession = Depends(get_session)):
    w = (await db.execute(select(Workorder).where(Workorder.id == workorder_id))).scalar_one_or_none()
    if not w:
        raise HTTPException(404, "Not found")
    ts = (await db.execute(select(Task).where(Task.workorder_id == workorder_id))).scalars().all()
    total = max(1, len(ts))
    done = len([t for t in ts if t.status.value == "Afgerond"])
    progress = round(done / total * 100)
    return PortalWO(
        id=w.id, vehicle=w.vehicle, customer=w.customer, complaint=w.complaint,
        status=w.status.value, progress_pct=progress,
        tasks=[PortalTask(name=t.name, status=t.status.value) for t in ts]
    )