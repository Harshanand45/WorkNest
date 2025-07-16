from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectRoleCreate(BaseModel):
    Role: str
    CreatedBy: int
    CompanyId: int

class ProjectRoleUpdate(BaseModel):
    Role: Optional[str] = None
    UpdatedBy: int
    CompanyId: Optional[int] = None

class ProjectRoleOut(BaseModel):
    ProjectRoleId: int
    Role: str
    CreatedOn: Optional[datetime]
    CreatedBy: int
    UpdatedOn: Optional[datetime] = None
    UpdatedBy: Optional[int] = None
    IsActive: bool
    DeletedOn: Optional[datetime] = None
    DeletedBy: Optional[int] = None
    CompanyId: int
