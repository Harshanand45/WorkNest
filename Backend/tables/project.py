from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    Name: str
    StartDate: datetime
    EndDate: datetime
    ProjectManager: int
    Priority: str
    Status: str
    CompanyId: int
    Description: Optional[str] = None
    IsActive: Optional[bool] = True

class ProjectCreate(ProjectBase):
    CreatedBy: int

class ProjectUpdate(BaseModel):
    Name: Optional[str]
    StartDate: Optional[datetime]
    EndDate: Optional[datetime]
    ProjectManager: Optional[int]
    Priority: Optional[str]
    Status: Optional[str]
    UpdatedBy: int
    Description: Optional[str] = None
    IsActive: Optional[bool]

class ProjectOut(ProjectBase):
    ProjectId: int
    CreatedBy: int
    UpdatedBy: Optional[int] = None
    DeletedBy: Optional[int] = None
    CreatedOn: datetime
    UpdatedOn: Optional[datetime] = None
    DeletedOn: Optional[datetime] = None

class ProjectPaginationRequest(BaseModel):
    page: int =1
    PageLimit: int=10
    name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    project_manager: Optional[int] = None