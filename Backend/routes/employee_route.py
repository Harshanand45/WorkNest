from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List
import pyodbc
from db_connection import get_connection
from tables.employee import EmployeeCreate, EmployeePaginationRequest, EmployeeUpdate, EmployeeOut

router = APIRouter()

from datetime import datetime
import base64
import os
import uuid

from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List
import pyodbc
from db_connection import get_connection
from tables.employee import EmployeeCreate, EmployeePaginationRequest, EmployeeUpdate, EmployeeOut

router = APIRouter()

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_base64_image(base64_string: str) -> str:
    try:
        header, encoded = base64_string.split(",", 1)
        file_ext = header.split("/")[1].split(";")[0]
        filename = f"{uuid.uuid4()}.{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(encoded))
        return filepath
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")

@router.post("/employees", response_model=dict)
def create_employee(employee: EmployeeCreate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Employee WHERE Email = ? OR Phone = ?", employee.email, employee.phone)
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email or phone already exists")

        cursor.execute("SELECT 1 FROM Company WHERE CompanyId = ?", employee.company_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company ID not found")

        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", employee.created_by)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Created by user not found")

        image_path = None
        if employee.ImageUrl:
         image_path = save_base64_image(employee.ImageUrl)


        cursor.execute("""
            INSERT INTO Employee (Name, RoleID, Phone, Address, Email, Description,
                                  CreatedOn, CreatedBy, IsActive, CompanyId,
                                  ImgUrl, EmployeeImg, ImgPath)
            VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, 1, ?, ?, ?, ?)
        """, employee.name, employee.role_id, employee.phone, employee.address, employee.email,
           employee.description, employee.created_by, employee.company_id,
           employee.ImageUrl, None, image_path)

        db.commit()
        return {"message": "Employee created successfully"}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.put("/employees/{emp_id}", response_model=dict)
def update_employee(emp_id: int, employee: EmployeeUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ? AND IsActive = 1", emp_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")

        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", employee.updated_by)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Updated by user not found")

        FIELD_MAP = {
            "name": "Name",
            "role_id": "RoleId",
            "phone": "Phone",
            "address": "Address",
            "email": "Email",
            "description": "Description",
            "ImageUrl": "ImgUrl"
        }

        update_fields = []
        params = []

        for field, value in employee.dict(exclude_unset=True).items():
            if field == "updated_by" or field == "EmployeeImage":
                continue
            db_field = FIELD_MAP.get(field)
            if db_field:
                update_fields.append(f"{db_field} = ?")
                params.append(value)

            if employee.EmployeeImage and "," in employee.EmployeeImage:
                # Remove existing ImgPath = ? if already present
                 if "ImgPath = ?" in update_fields:
                    idx = update_fields.index("ImgPath = ?")
                    update_fields.pop(idx)
                    params.pop(idx)

                 image_path = save_base64_image(employee.EmployeeImage)
                 update_fields.append("ImgPath = ?")
                 params.append(image_path)
            elif employee.EmployeeImage:
              if employee.EmployeeImage.startswith("data:image/"):
                 image_path = save_base64_image(employee.EmployeeImage)
                 update_fields.append("ImgPath = ?")
                 params.append(image_path)
            else:
        # Just ignore invalid base64 rather than erroring out
                pass



        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        update_fields.append("UpdatedOn = GETDATE()")
        update_fields.append("UpdatedBy = ?")
        params.append(employee.updated_by)
        params.append(emp_id)

        query = f"UPDATE Employee SET {', '.join(update_fields)} WHERE EmpId = ?"
        cursor.execute(query, *params)
        db.commit()

        return {"message": "Employee updated successfully"}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.delete("/employees/{emp_id}", response_model=dict)
def delete_employee(emp_id: int, deleted_by: str, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if employee exists
        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ? AND IsActive = 1", emp_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")

        # Validate deleted_by user
        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", deleted_by)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deleted by user not found")

        cursor.execute("""
            UPDATE Employee SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? WHERE EmpId = ?
        """, deleted_by, emp_id)
        db.commit()

        return {"message": "Employee deleted successfully"}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/allemployees", response_model=List[EmployeeOut])
def list_employees(db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT EmpId, Name, RoleID, Phone, Address, Email, Description,
                   CompanyId, CreatedBy, UpdatedBy, IsActive,ImgUrl,EmployeeImg,ImgPath
            FROM Employee
            WHERE IsActive = 1
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(EmployeeOut(
                emp_id=row.EmpId,
                name=row.Name,
                role_id=row.RoleID,
                phone=row.Phone,
                address=row.Address,
                email=row.Email,
                description=row.Description,
                company_id=row.CompanyId,
                created_by=row.CreatedBy,
                updated_by=row.UpdatedBy,
                is_active=bool(row.IsActive),

                EmployeeImage=row.EmployeeImg,
                ImageUrl=row.ImgUrl,
                ImagePath=row.ImgPath

            ))
        return result

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.post("/employees/paginated", response_model=Dict[str, Any])
def get_paginated_employees(pagination: EmployeePaginationRequest, db: pyodbc.Connection = Depends(get_connection)):
    try:
        page = pagination.page
        page_limit = pagination.page_limit
        offset = (page - 1) * page_limit

        filters = ["IsActive = 1", "RoleId != 8"]
        params = []

        if pagination.role_id:
            filters.append("RoleId = ?")
            params.append(pagination.role_id)

        if pagination.search:
            filters.append("LOWER(Name) LIKE ?")
            params.append(f"%{pagination.search.lower()}%")

        if pagination.company_id:
            filters.append("CompanyId = ?")
            params.append(pagination.company_id)

        where_clause = " AND ".join(filters)

        cursor = db.cursor()

        # Total count query
        count_query = f"SELECT COUNT(*) FROM Employee WHERE {where_clause}"
        cursor.execute(count_query, *params)
        total_count = cursor.fetchone()[0]

        # Paginated query
        data_query = f"""
            SELECT EmpId, Name, RoleID, Phone, Address, Email, Description,
                   CompanyId, CreatedBy, UpdatedBy, IsActive, CreatedOn, UpdatedOn, DeletedOn, DeletedBy
            FROM Employee
            WHERE {where_clause}
            ORDER BY EmpId
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(data_query, *params, offset, page_limit)

        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append(EmployeeOut(
                emp_id=row.EmpId,
                name=row.Name,
                role_id=row.RoleID,
                phone=row.Phone,
                address=row.Address,
                email=row.Email,
                description=row.Description,
                company_id=row.CompanyId,
                created_by=row.CreatedBy,
                updated_by=row.UpdatedBy,
                is_active=bool(row.IsActive),
                created_on=row.CreatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.CreatedOn, datetime) else None,
                updated_on=row.UpdatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.UpdatedOn, datetime) else None,
                deleted_on=row.DeletedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.DeletedOn, datetime) else None,
                deleted_by=row.DeletedBy
            ))

        total_pages = (total_count + page_limit - 1) // page_limit
        current_page = page if total_count > 0 else 0

        return {
            "data": [d.dict() for d in data],
            "total": total_count,
            "page": current_page,
            "page_limit": page_limit,
            "total_pages": total_pages
        }

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
