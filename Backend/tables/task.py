from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class TaskCreate(BaseModel):
    Name: str
    ProjectId: int
    AssignedTo: Optional[int] = None
    DocumentPath: Optional[str] = None
    DocumentUrl: Optional[str] = None
    Deadline: Optional[datetime] = None
    Priority: Optional[str] = None  # Changed to string
    Status: Optional[str] = None
    CreatedBy: int
    CompanyId: int
    Description: Optional[str] = None
    DocumentName: Optional[str] = None
    ExptedHours: Optional[Decimal] = None



class TaskUpdate(BaseModel):
    Name: Optional[str] = None
    ProjectId: Optional[int] = None
    AssignedTo: Optional[int] = None
    DocumentPath: Optional[str] = None
    DocumentUrl: Optional[str] = None
    Deadline: Optional[datetime] = None
    Priority: Optional[str] = None
    Status: Optional[str] = None
    UpdatedBy: int
    CompanyId: Optional[int] = None
    Description: Optional[str] = None
    DocumentName: Optional[str] = None
    IsActive: Optional[bool] = True
    ExptedHours: Optional[Decimal] = None


class TaskOut(BaseModel):
    TaskId: int
    Name: str
    ProjectId: int
    AssignedTo: Optional[int]
    DocumentPath: Optional[str]
    DocumentUrl: Optional[str]
    Deadline: Optional[datetime]
    Priority: Optional[str]
    Status: Optional[str]
    CreatedOn: datetime
    CreatedBy: int
    UpdatedOn: Optional[datetime]
    UpdatedBy: Optional[int]
    DeletedOn: Optional[datetime]
    DeletedBy: Optional[int]
    CompanyId: int
    Description: Optional[str]
    DocumentName: Optional[str]
    IsActive: bool
    ExptedHours: Optional[Decimal] = None
class TaskPaginationRequest(BaseModel):
    page: int
    PageLimit: int
    ProjectName: Optional[str] = None
    AssignedTo: Optional[int] = None
    Priority: Optional[str] = None
    TaskName: Optional[str] = None
    ManagerId: Optional[int] = None 
    
    