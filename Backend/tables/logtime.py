from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel

class LogTimeBase(BaseModel):
    EmpId: int
    TaskId: int
    Date: date
    CompanyId: int
    Description: Optional[str] = None
    MinutesSpent: Optional[int] = None
    HoursSpent: Optional[int] = None

class LogTimeCreate(LogTimeBase):
    CreatedBy: int

class LogTimeUpdate(BaseModel):
    EmpId: Optional[int]=None
    TaskId: Optional[int]=None
    Date: Optional[date]=None
    UpdatedBy: int
    Description: Optional[str] = None
    MinutesSpent: Optional[int] = None
    HoursSpent: Optional[int] = None

class LogTimeOut(LogTimeBase):
    LogId: int
    CreatedOn: Optional[datetime] = None
    CreatedBy: int
    UpdatedOn: Optional[datetime] = None
    UpdatedBy: Optional[int] = None
    IsActive: bool
    DeletedOn: Optional[datetime] = None
    DeletedBy: Optional[int] = None
class PaginationRequest(BaseModel):
    page: int
    PageLimit: int
    employee_name: Optional[str] = None
    task_title: Optional[str] = None