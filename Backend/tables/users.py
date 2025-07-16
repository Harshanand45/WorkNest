from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserBase(BaseModel):
    """Base model for User data"""
    email: EmailStr = Field(..., example="user@example.com")
    is_active: Optional[int] = Field(1, ge=0, le=1, example=1)
    
    role_id: int = Field(..., example=3)  # ✅ Role assignment
    company_id: int = Field(..., example=1)  # ✅ Company association

class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str = Field(..., min_length=8, example="StrongPassword123!")  # ✅ Stores plain text password
    created_by: int = Field(..., example=1)

class UserUpdate(BaseModel):
    """Model for updating user details"""
    email: Optional[EmailStr] = Field(None, example="updated_email@example.com")
    password: Optional[str] = Field(None, min_length=8, example="UpdatedPassword123!")
    is_active: Optional[int] = Field(None, ge=0, le=1, example=1)
    updated_by: int = Field(..., example=2)  # ✅ Required field
    role_id: Optional[int] = Field(None, example=3)
    company_id: Optional[int] = Field(None, example=1)




class User(UserBase):
    """Response model for a user"""
    user_id: int
    password: str = Field(..., example="PlainTextPassword")  # ✅ Returns plain text password (not secure!)
    created_on: Optional[str] = Field(None, example="2025-06-02 12:00:00")
    created_by: int = Field(..., example=1)
    updated_on: Optional[str] = Field(None, example="2025-06-02 15:43:52")
    updated_by: Optional[int] = Field(None, example=2)
    deleted_on: Optional[str] = Field(None, example="2025-06-02 16:00:00")
    deleted_by: Optional[int] = Field(None, example=3)

class UserPaginationRequest(BaseModel):
    page: int = 1
    PageLimit: int = 10
    company_id: Optional[int] = None
    role_id: Optional[int] = None
    search: Optional[str] = None