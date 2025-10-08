from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date

class EmployeeCreate(BaseModel):
    name: str
    role: Literal["Admin","Balie","Monteur"] = "Monteur"
    user_id: Optional[str] = None

class EmployeeOut(EmployeeCreate):
    id: int

class WorkorderCreate(BaseModel):
    id: str
    vehicle: str
    customer: str
    phone: Optional[str] = None
    received: Optional[date] = None
    due: Optional[date] = None
    complaint: Optional[str] = None
    status: Literal["Nieuw","In behandeling","Afgerond"] = "Nieuw"

class WorkorderOut(WorkorderCreate): pass

class TaskCreate(BaseModel):
    workorder_id: str
    name: str
    assigned_employee_id: Optional[int] = None
    status: Literal["To do","Bezig","Afgerond"] = "To do"
    time_spent: Optional[str] = None

class TaskOut(TaskCreate):
    id: int