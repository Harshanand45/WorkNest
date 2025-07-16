from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from datetime import datetime
import pyodbc

from db_connection import get_connection
from tables.projectRole import ProjectRoleCreate, ProjectRoleUpdate, ProjectRoleOut

router = APIRouter()

# ---------------------------
# VALIDATION HELPERS
# ---------------------------
def validate_emp(cursor, emp_id: int, label: str = "Employee"):
    cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ?", emp_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{label} with EmpId {emp_id} not found")

def validate_company(cursor, company_id: int):
    cursor.execute("SELECT 1 FROM Company WHERE CompanyId = ?", company_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"CompanyId {company_id} not found")

# ---------------------------
# CREATE
# ---------------------------
@router.post("/project-roles", response_model=Dict[str, str])
def create_project_role(data: ProjectRoleCreate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        validate_emp(cursor, data.CreatedBy, "CreatedBy")
        validate_company(cursor, data.CompanyId)

        cursor.execute("""
            INSERT INTO ProjectRole (Role, CreatedBy, CompanyId, CreatedOn, IsActive)
            VALUES (?, ?, ?, GETDATE(), 1)
        """, data.Role, data.CreatedBy, data.CompanyId)

        db.commit()
        return {"message": "Project role created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ---------------------------
# UPDATE
# ---------------------------
@router.put("/project-roles/{role_id}", response_model=Dict[str, str])
def update_project_role(role_id: int, data: ProjectRoleUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM ProjectRole WHERE ProjectRoleId = ? AND IsActive = 1", role_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="ProjectRole not found or inactive")

        validate_emp(cursor, data.UpdatedBy, "UpdatedBy")
        if data.CompanyId:
            validate_company(cursor, data.CompanyId)

        fields = []
        params = []

        if data.Role is not None:
            fields.append("Role = ?")
            params.append(data.Role)

        if data.CompanyId is not None:
            fields.append("CompanyId = ?")
            params.append(data.CompanyId)

        if not fields:
            raise HTTPException(status_code=400, detail="No update fields provided")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = ?")
        params.append(data.UpdatedBy)

        params.append(role_id)

        sql = f"UPDATE ProjectRole SET {', '.join(fields)} WHERE ProjectRoleId = ?"
        cursor.execute(sql, *params)
        db.commit()

        return {"message": "Project role updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ---------------------------
# DELETE (Soft)
# ---------------------------
@router.delete("/project-roles/{role_id}", response_model=Dict[str, str])
def delete_project_role(role_id: int, deleted_by: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM ProjectRole WHERE ProjectRoleId = ? AND IsActive = 1", role_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="ProjectRole not found or already deleted")

        validate_emp(cursor, deleted_by, "DeletedBy")

        cursor.execute("""
            UPDATE ProjectRole
            SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ?
            WHERE ProjectRoleId = ?
        """, deleted_by, role_id)

        db.commit()
        return {"message": "Project role deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ---------------------------
# LIST
# ---------------------------
@router.get("/projectroles", response_model=List[ProjectRoleOut])
def list_project_roles(db: pyodbc.Connection = Depends(get_connection)):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
