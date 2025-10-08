from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Text, Enum, Date, ForeignKey, String, TIMESTAMP, func
import enum
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    Admin = "Admin"
    Balie = "Balie"
    Monteur = "Monteur"

class TaskStatusEnum(str, enum.Enum):
    ToDo = "To do"
    Bezig = "Bezig"
    Afgerond = "Afgerond"

class WorkorderStatusEnum(str, enum.Enum):
    Nieuw = "Nieuw"
    InBehandeling = "In behandeling"
    Afgerond = "Afgerond"

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID, primary_key=True)
    name = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

class Employee(Base):
    __tablename__ = "employees"
    id = Column(BigInteger, primary_key=True)
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    role = Column(Enum(RoleEnum, name="role_enum"), nullable=False, server_default="Monteur")
    user_id = Column(UUID, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

class Workorder(Base):
    __tablename__ = "workorders"
    id = Column(String, primary_key=True)  # e.g. "2025-014"
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    vehicle = Column(Text, nullable=False)
    customer = Column(Text, nullable=False)
    phone = Column(Text)
    received = Column(Date)
    due = Column(Date)
    complaint = Column(Text)
    status = Column(Enum(WorkorderStatusEnum, name="workorder_status_enum"), nullable=False, server_default="Nieuw")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(BigInteger, primary_key=True)
    org_id = Column(UUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    workorder_id = Column(String, ForeignKey("workorders.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    assigned_employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"))
    status = Column(Enum(TaskStatusEnum, name="task_status_enum"), nullable=False, server_default="To do")
    time_spent = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)