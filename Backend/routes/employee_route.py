from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List
import pymssql
from db_connection import get_connection
from tables.employee import EmployeeCreate, EmployeePaginationRequest, EmployeeUpdate, EmployeeOut

import base64
import os
import uuid

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
def create_employee(employee: EmployeeCreate, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Employee WHERE Email = %s OR Phone = %s", (employee.email, employee.phone))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email or phone already exists")

        cursor.execute("SELECT 1 FROM Company WHERE CompanyId = %s", (employee.company_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Company ID not found")

        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (employee.created_by,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Created by user not found")

        image_path = None
        if employee.ImageUrl:
            image_path = save_base64_image(employee.ImageUrl)

        cursor.execute("""
            INSERT INTO Employee (Name, RoleID, Phone, Address, Email, Description,
                                  CreatedOn, CreatedBy, IsActive, CompanyId,
                                  ImgUrl, EmployeeImg, ImgPath)
            VALUES (%s, %s, %s, %s, %s, %s, GETDATE(), %s, 1, %s, %s, %s, %s)
        """, (employee.name, employee.role_id, employee.phone, employee.address, employee.email,
              employee.description, employee.created_by, employee.company_id,
              employee.ImageUrl, None, image_path))

        db.commit()
        return {"message": "Employee created successfully"}

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.put("/employees/{emp_id}", response_model=dict)
def update_employee(emp_id: int, employee: EmployeeUpdate, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s AND IsActive = 1", (emp_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")

        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (employee.updated_by,))
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
            if field in ["updated_by", "EmployeeImage"]:
                continue
            db_field = FIELD_MAP.get(field)
            if db_field:
                update_fields.append(f"{db_field} = %s")
                params.append(value)

        if employee.EmployeeImage and "," in employee.EmployeeImage:
            image_path = save_base64_image(employee.EmployeeImage)
            update_fields.append("ImgPath = %s")
            params.append(image_path)
        elif employee.EmployeeImage and employee.EmployeeImage.startswith("data:image/"):
            image_path = save_base64_image(employee.EmployeeImage)
            update_fields.append("ImgPath = %s")
            params.append(image_path)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        update_fields.append("UpdatedOn = GETDATE()")
        update_fields.append("UpdatedBy = %s")
        params.append(employee.updated_by)
        params.append(emp_id)

        query = f"UPDATE Employee SET {', '.join(update_fields)} WHERE EmpId = %s"
        cursor.execute(query, tuple(params))
        db.commit()

        return {"message": "Employee updated successfully"}

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.delete("/employees/{emp_id}", response_model=dict)
def delete_employee(emp_id: int, deleted_by: str, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s AND IsActive = 1", (emp_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")

        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (deleted_by,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Deleted by user not found")

        cursor.execute("""
            UPDATE Employee SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s WHERE EmpId = %s
        """, (deleted_by, emp_id))
        db.commit()

        return {"message": "Employee deleted successfully"}

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/allemployees", response_model=List[EmployeeOut])
def list_employees(db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT EmpId, Name, RoleID, Phone, Address, Email, Description,
                   CompanyId, CreatedBy, UpdatedBy, IsActive, ImgUrl, EmployeeImg, ImgPath
            FROM Employee
            WHERE IsActive = 1
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(EmployeeOut(
                emp_id=row[0], name=row[1], role_id=row[2], phone=row[3], address=row[4],
                email=row[5], description=row[6], company_id=row[7], created_by=row[8],
                updated_by=row[9], is_active=bool(row[10]), ImageUrl=row[11],
                EmployeeImage=row[12], ImagePath=row[13]
            ))
        return result

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.post("/employees/paginated", response_model=Dict[str, Any])
def get_paginated_employees(pagination: EmployeePaginationRequest, db: pymssql.Connection = Depends(get_connection)):
    try:
        page = pagination.page
        page_limit = pagination.page_limit
        offset = (page - 1) * page_limit

        filters = ["IsActive = 1", "RoleId != 8"]
        params = []

        if pagination.role_id:
            filters.append("RoleId = %s")
            params.append(pagination.role_id)

        if pagination.search:
            filters.append("LOWER(Name) LIKE %s")
            params.append(f"%{pagination.search.lower()}%")

        if pagination.company_id:
            filters.append("CompanyId = %s")
            params.append(pagination.company_id)

        where_clause = " AND ".join(filters)

        cursor = db.cursor()

        count_query = f"SELECT COUNT(*) FROM Employee WHERE {where_clause}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()[0]

        data_query = f"""
            SELECT EmpId, Name, RoleID, Phone, Address, Email, Description,
                   CompanyId, CreatedBy, UpdatedBy, IsActive, CreatedOn, UpdatedOn, DeletedOn, DeletedBy
            FROM Employee
            WHERE {where_clause}
            ORDER BY EmpId
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """
        cursor.execute(data_query, tuple(params + [offset, page_limit]))

        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append(EmployeeOut(
                emp_id=row[0], name=row[1], role_id=row[2], phone=row[3], address=row[4], email=row[5],
                description=row[6], company_id=row[7], created_by=row[8], updated_by=row[9],
                is_active=bool(row[10]),
                created_on=row[11].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[11], datetime) else None,
                updated_on=row[12].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[12], datetime) else None,
                deleted_on=row[13].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[13], datetime) else None,
                deleted_by=row[14]
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

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")