from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Task
from app.schemas import TaskCreate, TaskOut
from app.deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=list[TaskOut])
async def list_tasks(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    workorder_id: str | None = None,
    assigned_employee_id: int | None = None,
    status: str | None = None
):
    q = select(Task).where(Task.org_id == user.org_id)
    if workorder_id:
        q = q.where(Task.workorder_id == workorder_id)
    if assigned_employee_id:
        q = q.where(Task.assigned_employee_id == assigned_employee_id)
    if status:
        q = q.where(Task.status == status)
    res = await db.execute(q.order_by(Task.created_at.desc()))
    return [TaskOut(**{
        "id": t.id, "workorder_id": t.workorder_id, "name": t.name,
        "assigned_employee_id": t.assigned_employee_id,
        "status": t.status.value, "time_spent": t.time_spent
    }) for t in res.scalars().all()]

@router.post("", response_model=TaskOut, status_code=201)
async def create_task(payload: TaskCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    stmt = insert(Task).values(org_id=user.org_id, **payload.model_dump()).returning(Task)
    res = await db.execute(stmt)
    await db.commit()
    t = res.scalar_one()
    return TaskOut(**{
        "id": t.id, "workorder_id": t.workorder_id, "name": t.name,
        "assigned_employee_id": t.assigned_employee_id,
        "status": t.status.value, "time_spent": t.time_spent
    })

@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, payload: TaskCreate, user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    res = await db.execute(
        update(Task)
        .where(Task.id == task_id, Task.org_id == user.org_id)
        .values(**payload.model_dump())
        .returning(Task)
    )
    await db.commit()
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Not found")
    return TaskOut(**{
        "id": t.id, "workorder_id": t.workorder_id, "name": t.name,
        "assigned_employee_id": t.assigned_employee_id,
        "status": t.status.value, "time_spent": t.time_spent
    })