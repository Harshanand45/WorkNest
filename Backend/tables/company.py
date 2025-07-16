from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class CompanyBase(BaseModel):
    """Base model for Company data"""
    name: str = Field(..., example="TechCorp")
    is_active: Optional[int] = Field(1, ge=0, le=1, example=1)
    company_description: Optional[str] = Field(None, example="Software development firm")

class CompanyCreate(CompanyBase):
    """Model for creating a new company"""
    created_by: int = Field(..., example=1)
    company_logo_name: Optional[str] = Field(None, example="logo.png")
    company_logo_url: Optional[str] = Field(None, example="https://example.com/logo.png")
    company_logo_path: Optional[str] = Field(None, example="/uploads/logo.png")
    contact_no: str = Field(..., example="+91-9876543210", pattern=r'^\+\d{10,15}$')  # ✅ Uses Pattern-based validation
    email: EmailStr = Field(..., example="contact@techcorp.com")  # ✅ Valid email format
    address: Optional[str] = Field(None, example="123 Tech Street, India")

class CompanyUpdate(BaseModel):
    """Model for updating company details"""
    name: Optional[str] = Field(None, example="Updated Company Name")
    is_active: Optional[int] = Field(None, ge=0, le=1, example=1)
    company_description: Optional[str] = Field(None, example="Updated description")
    updated_by: int = Field(..., example=2)  # ✅ Ensures updated_by is always required
    company_logo_name: Optional[str] = Field(None, example="updated_logo.png")
    company_logo_url: Optional[str] = Field(None, example="https://example.com/updated_logo.png")
    company_logo_path: Optional[str] = Field(None, example="/uploads/updated_logo.png")
    contact_no: Optional[str] = Field(None, pattern=r'^\+\d{10,15}$', example="+91-9876543210")  # ✅ Updated Pattern validation
    email: Optional[EmailStr] = Field(None, example="updated_email@example.com")
    address: Optional[str] = Field(None, example="Updated company address")

    

class Company(CompanyBase):
    """Response model for a company"""
    company_id: int
    created_on: Optional[str] = Field(None, example="2025-06-02 12:00:00")
    created_by: int = Field(..., example=1)
    updated_on: Optional[str] = Field(None, example="2025-06-02 15:43:52")
    updated_by: Optional[int] = Field(None, example=2)
    deleted_on: Optional[str] = Field(None, example="2025-06-02 16:00:00")
    deleted_by: Optional[int] = Field(None, example=3)
    company_logo_name: Optional[str] = Field(None, example="logo.png")
    company_logo_url: Optional[str] = Field(None, example="https://example.com/logo.png")
    company_logo_path: Optional[str] = Field(None, example="/uploads/logo.png")
    contact_no: str = Field(..., example="+91-9876543210")
    email: EmailStr = Field(..., example="contact@techcorp.com")
    address: Optional[str] = Field(None, example="123 Tech Street, India")


class CompanyPaginationRequest(BaseModel):
    page: int = 1
    limit: int = 10