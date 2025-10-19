from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, BigInteger, Text, Enum, Date, ForeignKey, String, Boolean, TIMESTAMP, func
import enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    Balie = "Balie"
    Monteur = "Monteur"

class TaskStatusEnum(str, enum.Enum):
    ToDo = "To do"        # ← Add the space back!
    Bezig = "Bezig"
    Afgerond = "Afgerond"


class WorkorderStatusEnum(str, enum.Enum):
    Nieuw = "Nieuw"
    InBehandeling = "In behandeling"
    Afgerond = "Afgerond"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to access all workorders for this customer
    workorders = relationship("Workorder", back_populates="customer")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    role = Column(Enum(RoleEnum, name="role_enum"), nullable=False, server_default="Monteur")

    # ↓↓↓ auth fields ↓↓↓
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")

    user_id = Column(UUID, nullable=True) 
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to access all tasks assigned to this employee
    assigned_tasks = relationship("Task", back_populates="assigned_employee")


class Workorder(Base):
    __tablename__ = "workorders"

    id = Column(String, primary_key=True) 
    vehicle = Column(Text, nullable=False)
    complaint = Column(Text)
    status = Column(Enum(WorkorderStatusEnum, name="workorder_status_enum"),
                     nullable=False, server_default="Nieuw")
    received = Column(Date)
    due = Column(Date)

    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # FIX: Creates the .customer attribute for Python access
    customer = relationship("Customer", back_populates="workorders") 
    
    # Relationship to access all tasks on this workorder
    tasks = relationship("Task", back_populates="workorder")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    workorder_id = Column(String, ForeignKey("workorders.id", ondelete="CASCADE"), nullable=False)
    assigned_employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"))
    
    name = Column(Text, nullable=False)
    
    # 🌟 FINAL FIX APPLIED HERE 🌟
  

    status = Column(
        SQLEnum("To do", "Bezig", "Afgerond", name="task_status_enum"),
        nullable=False,
        server_default="To do"
    )
        
    time_spent = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    workorder = relationship("Workorder", back_populates="tasks")
    assigned_employee = relationship("Employee", back_populates="assigned_tasks")