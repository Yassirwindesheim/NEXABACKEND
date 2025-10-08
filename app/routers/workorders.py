from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Workorder
from app.schemas import WorkorderCreate, WorkorderOut
from app.deps import get_current_user

router = APIRouter(prefix="/workorders", tags=["workorders"])

@router.get("", response_model=list[WorkorderOut])
async def list_workorders(user=Depends(get_current_user), db: AsyncSession = Depends(get_session), status: str | None = None):
    q = select(Workorder).where(Workorder.org_id == user.org_id).order_by(Workorder.created_at.desc())
    if status:
        q = q.where(Workorder.status == status)
    res = await db.execute(q)
    wos = res.scalars().all()
    return [WorkorderOut(**{
        "id": w.id, "vehicle": w.vehicle, "customer": w.customer, "phone": w.phone,
        "received": w.received, "due": w.due, "complaint": w.complaint, "status": w.status.value
    }) for w in wos]

@router.post("", response_model=WorkorderOut, status_code=201)
async def create_workorder(payload: WorkorderCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    # trust client-provided id; alternatively generate server-side
    stmt = insert(Workorder).values(org_id=user.org_id, **payload.model_dump()).returning(Workorder)
    res = await db.execute(stmt)
    await db.commit()
    w = res.scalar_one()
    return WorkorderOut(**{
        "id": w.id, "vehicle": w.vehicle, "customer": w.customer, "phone": w.phone,
        "received": w.received, "due": w.due, "complaint": w.complaint, "status": w.status.value
    })

@router.patch("/{workorder_id}", response_model=WorkorderOut)
async def update_workorder(workorder_id: str, payload: WorkorderCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    res = await db.execute(
        update(Workorder)
        .where(Workorder.id == workorder_id, Workorder.org_id == user.org_id)
        .values(**payload.model_dump())
        .returning(Workorder)
    )
    await db.commit()
    w = res.scalar_one_or_none()
    if not w:
        raise HTTPException(404, "Not found")
    return WorkorderOut(**{
        "id": w.id, "vehicle": w.vehicle, "customer": w.customer, "phone": w.phone,
        "received": w.received, "due": w.due, "complaint": w.complaint, "status": w.status.value
    })