# app/routers/tasks.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Task, TaskStatusEnum
from app.schemas import TaskCreate, TaskOut
from app.deps import get_current_user, AuthedUser

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=list[TaskOut])
async def list_tasks(
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    workorder_id: Optional[str] = None,
    assigned_employee_id: Optional[int] = None,
    status: Optional[str] = None,
):
    q = select(Task)
    if workorder_id:
        q = q.where(Task.workorder_id == workorder_id)
    if assigned_employee_id:
        q = q.where(Task.assigned_employee_id == assigned_employee_id)
    if status:
        q = q.where(Task.status == status)

    res = await db.execute(q.order_by(Task.created_at.desc()))
    tasks = res.scalars().all()
    return [
        TaskOut(
            id=t.id,
            workorder_id=t.workorder_id,
            name=t.name,
            assigned_employee_id=t.assigned_employee_id,
            status=t.status,
            time_spent=t.time_spent,
        )
        for t in tasks
    ]

@router.post("", response_model=TaskOut, status_code=201)
async def create_task(
    payload: TaskCreate,
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    # 🌟 CRITICAL FIX: Use the enum directly, not the string
    # Convert string to enum value
    if payload.status == "ToDo" or payload.status == "To do":
        status_enum = TaskStatusEnum.ToDo
    elif payload.status == "Bezig":
        status_enum = TaskStatusEnum.Bezig
    elif payload.status == "Afgerond":
        status_enum = TaskStatusEnum.Afgerond
    else:
        status_enum = TaskStatusEnum.ToDo  # Default
    
    print(f"🔍 Creating task - Input: '{payload.status}' -> Enum: {status_enum} -> Value: '{status_enum.value}'")
    
    stmt = (
        insert(Task)
        .values(
            workorder_id=payload.workorder_id,
            name=payload.name,
            assigned_employee_id=payload.assigned_employee_id,
            status=status_enum,  # Use the enum, not string!
            time_spent=payload.time_spent
        )
        .returning(Task)
    )
    res = await db.execute(stmt)
    await db.commit()
    t = res.scalar_one()
    
    print(f"✅ Task created with ID {t.id}, status: {t.status}")
    
    return TaskOut(
        id=t.id,
        workorder_id=t.workorder_id,
        name=t.name,
        assigned_employee_id=t.assigned_employee_id,
        status=t.status,
        time_spent=t.time_spent,
    )

@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    payload: TaskCreate,
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    # 🌟 CRITICAL FIX: Use the enum directly
    if payload.status == "ToDo" or payload.status == "To do":
        status_enum = TaskStatusEnum.ToDo
    elif payload.status == "Bezig":
        status_enum = TaskStatusEnum.Bezig
    elif payload.status == "Afgerond":
        status_enum = TaskStatusEnum.Afgerond
    else:
        status_enum = TaskStatusEnum.ToDo
    
    print(f"🔍 Updating task {task_id} - Input: '{payload.status}' -> Enum: {status_enum} -> Value: '{status_enum.value}'")
    
    res = await db.execute(
        update(Task)
        .where(Task.id == task_id)
        .values(
            workorder_id=payload.workorder_id,
            name=payload.name,
            assigned_employee_id=payload.assigned_employee_id,
            status=status_enum,  # Use the enum!
            time_spent=payload.time_spent
        )
        .returning(Task)
    )
    await db.commit()
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")

    print(f"✅ Task {task_id} updated, status: {t.status}")

    return TaskOut(
        id=t.id,
        workorder_id=t.workorder_id,
        name=t.name,
        assigned_employee_id=t.assigned_employee_id,
        status=t.status,
        time_spent=t.time_spent,
    )