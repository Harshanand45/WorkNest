from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoleBase(BaseModel):
    role: str
    company_id: int
    is_active: bool = True
    created_by: int

class RoleCreate(BaseModel):
    role: str
    company_id: int
    is_active: bool = True
    created_by: int

class RoleUpdate(BaseModel):
    role: Optional[str] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None
    updated_by: Optional[int] = None

class Role(RoleBase):
    role_id: int
    created_on: Optional[datetime] = None
    updated_on: Optional[datetime] = None
    updated_by: Optional[int] = None
    deleted_on: Optional[datetime] = None
    deleted_by: Optional[int] = None

    class Config:
        orm_mode = True
class RolePaginationRequest(BaseModel):
    page: int = 1
    PageLimit: int = 10