# employee.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional



class EmployeeBase(BaseModel):
    name: str
    role_id: int
    phone: str
    address: str
    email: EmailStr
    description: str
    EmployeeImage:Optional[str]=None
    ImageUrl:Optional[str]=None
    ImagePath:Optional[str]=None

class EmployeeCreate(EmployeeBase):
    created_by: int
    company_id: int

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    role_id: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    updated_by: int
    EmployeeImage:Optional[str]
    ImageUrl:Optional[str]
    ImagePath:Optional[str]

class EmployeeOut(EmployeeBase):
    emp_id: int
    company_id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    is_active: bool

   
class EmployeePaginationRequest(BaseModel):
    
    page: int
    page_limit: int
    search: Optional[str] = None
    company_id: int
    role_id: Optional[int] = None 