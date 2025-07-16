from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectEmployeeCreate(BaseModel):
    EmpId: int
    ProjectId: int
    CreatedBy: int
    CompanyId: int
    ProjectRoleId: int

class ProjectEmployeeUpdate(BaseModel):
    UpdatedBy: int
    ProjectRoleId: Optional[int] = None
    ProjectId: Optional[int] = None
    CompanyId: Optional[int] = None

class ProjectEmployeeOut(BaseModel):
    ProjectEmployeeId: int
    EmpId: int
    ProjectId: int
    CreatedOn: Optional[datetime]
    CreatedBy: int
    IsActive: bool
    DeletedOn: Optional[datetime] = None
    DeletedBy: Optional[int] = None
    CompanyId: int
    ProjectRoleId: int
    UpdatedOn: Optional[datetime] = None
    UpdatedBy: Optional[int] = None
