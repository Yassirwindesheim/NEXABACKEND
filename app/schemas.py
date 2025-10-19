from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date

class EmployeeCreate(BaseModel):
    name: str
    role: Literal["Admin","Balie","Monteur"] = "Monteur"
    user_id: Optional[str] = None

class EmployeeOut(EmployeeCreate):
    id: int

# --- WorkorderCreate (The INPUT model for POST requests) ---
class WorkorderCreate(BaseModel):
    vehicle: str
    complaint: Optional[str] = None
    status: Literal["Nieuw","In behandeling","Afgerond"] = "Nieuw"
    received: Optional[date] = None
    due: Optional[date] = None
    customer_id: int 

# --- WorkorderOut (The OUTPUT model for GET and POST responses) ---
class WorkorderOut(BaseModel):
    id: str 
    vehicle: str
    complaint: Optional[str] = None
    status: Literal["Nieuw","In behandeling","Afgerond"]
    received: Optional[date] = None
    due: Optional[date] = None
    customer: str  # Customer Name
    phone: Optional[str] = None # Customer Phone

class TaskCreate(BaseModel):
    workorder_id: str
    name: str
    assigned_employee_id: Optional[int] = None
    status: str = "To do"  # ← Changed from Literal to str
    time_spent: Optional[str] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        """Convert any status format to database format"""
        if not v:
            return "To do"
        
        mapping = {
            "ToDo": "To do",
            "To do": "To do",
            "Bezig": "Bezig",
            "Afgerond": "Afgerond",
        }
        
        result = mapping.get(v, "To do")
        print(f"🔄 Status validator: '{v}' -> '{result}'")
        return result

class TaskOut(TaskCreate):
    id: int

class CustomerOut(BaseModel):
    id: int
    name: str 
    phone: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True