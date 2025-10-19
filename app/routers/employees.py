# app/routers/employees.py
from fastapi import APIRouter, Depends
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeOut
from app.deps import get_current_user, require_admin, AuthedUser


router = APIRouter(prefix="/employees", tags=["employees"])

@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    user: AuthedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    res = await db.execute(select(Employee).order_by(Employee.id.desc()))
    return [
        EmployeeOut(id=e.id, name=e.name, role=e.role.value, user_id=e.user_id)
        for e in res.scalars().all()
    ]

@router.post("", response_model=EmployeeOut, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    # 👇 this line enforces Admin-only:
    user: AuthedUser = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    stmt = (
        insert(Employee)
        .values(name=payload.name, role=payload.role, user_id=payload.user_id)
        .returning(Employee)
    )
    res = await db.execute(stmt)
    await db.commit()
    e = res.scalar_one()
    return EmployeeOut(id=e.id, name=e.name, role=e.role.value, user_id=e.user_id)

@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: int,
    payload: EmployeeCreate,
    user: AuthedUser = Depends(get_current_user),  # keep as-is; make admin-only if you want
    db: AsyncSession = Depends(get_session)
):
    res = await db.execute(
        update(Employee)
        .where(Employee.id == employee_id)
        .values(name=payload.name, role=payload.role, user_id=payload.user_id)
        .returning(Employee)
    )
    await db.commit()
    e = res.scalar_one()
    return EmployeeOut(id=e.id, name=e.name, role=e.role.value, user_id=e.user_id)
