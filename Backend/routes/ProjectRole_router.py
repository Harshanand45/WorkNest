from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from datetime import datetime
import pymssql # Changed from pyodbc

from db_connection import get_connection
from tables.projectRole import ProjectRoleCreate, ProjectRoleUpdate, ProjectRoleOut

router = APIRouter()

# ---------------------------
# VALIDATION HELPERS
# ---------------------------
def validate_emp(cursor, emp_id: int, label: str = "Employee"):
    cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (emp_id,)) # Changed ? to %s
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{label} with EmpId {emp_id} not found")

def validate_company(cursor, company_id: int):
    cursor.execute("SELECT 1 FROM Company WHERE CompanyId = %s", (company_id,)) # Changed ? to %s
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"CompanyId {company_id} not found")

# ---------------------------
# CREATE
# ---------------------------
@router.post("/project-roles", response_model=Dict[str, str])
def create_project_role(data: ProjectRoleCreate, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()

        validate_emp(cursor, data.CreatedBy, "CreatedBy")
        validate_company(cursor, data.CompanyId)

        cursor.execute("""
            INSERT INTO ProjectRole (Role, CreatedBy, CompanyId, CreatedOn, IsActive)
            VALUES (%s, %s, %s, GETDATE(), 1)
        """, (data.Role, data.CreatedBy, data.CompanyId)) # Changed ? to %s and ensured tuple

        db.commit()
        return {"message": "Project role created successfully."}
    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback() # Rollback changes on error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Ensure rollback for other unexpected errors too
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# ---------------------------
# UPDATE
# ---------------------------
@router.put("/project-roles/{role_id}", response_model=Dict[str, str])
def update_project_role(role_id: int, data: ProjectRoleUpdate, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM ProjectRole WHERE ProjectRoleId = %s AND IsActive = 1", (role_id,)) # Changed ? to %s
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="ProjectRole not found or inactive")

        validate_emp(cursor, data.UpdatedBy, "UpdatedBy")
        if data.CompanyId:
            validate_company(cursor, data.CompanyId)

        fields = []
        params = []

        if data.Role is not None:
            fields.append("Role = %s") # Changed ? to %s
            params.append(data.Role)

        if data.CompanyId is not None:
            fields.append("CompanyId = %s") # Changed ? to %s
            params.append(data.CompanyId)

        if not fields:
            raise HTTPException(status_code=400, detail="No update fields provided")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = %s") # Changed ? to %s
        params.append(data.UpdatedBy)

        params.append(role_id) # Add role_id for the WHERE clause

        sql = f"UPDATE ProjectRole SET {', '.join(fields)} WHERE ProjectRoleId = %s" # Changed ? to %s
        cursor.execute(sql, tuple(params)) # Ensure params is a tuple
        db.commit()

        return {"message": "Project role updated successfully."}
    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# ---------------------------
# DELETE (Soft)
# ---------------------------
@router.delete("/project-roles/{role_id}", response_model=Dict[str, str])
def delete_project_role(role_id: int, deleted_by: int, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM ProjectRole WHERE ProjectRoleId = %s AND IsActive = 1", (role_id,)) # Changed ? to %s
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="ProjectRole not found or already deleted")

        validate_emp(cursor, deleted_by, "DeletedBy")

        cursor.execute("""
            UPDATE ProjectRole
            SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s
            WHERE ProjectRoleId = %s
        """, (deleted_by, role_id)) # Changed ? to %s and ensured tuple

        db.commit()
        return {"message": "Project role deleted successfully."}
    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# ---------------------------
# LIST
# ---------------------------
@router.get("/projectroles", response_model=List[ProjectRoleOut])
def list_project_roles(db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT ProjectRoleId, Role, CreatedOn, CreatedBy, UpdatedOn, UpdatedBy,
                   IsActive, DeletedOn, DeletedBy, CompanyId
            FROM ProjectRole
            WHERE IsActive = 1
        """)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [ProjectRoleOut(**dict(zip(columns, row))) for row in rows]
    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")