from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict
from datetime import datetime
import pyodbc

from db_connection import get_connection
from tables.EmployeeProject import ProjectEmployeeCreate, ProjectEmployeeUpdate, ProjectEmployeeOut

router = APIRouter()

# -------------------------
# VALIDATION HELPERS
# -------------------------
def validate_project_role(cursor, project_role_id: int):
    cursor.execute("SELECT 1 FROM ProjectRole WHERE ProjectRoleId = ?", project_role_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"ProjectRoleId {project_role_id} not found or inactive")

def validate_emp(cursor, emp_id: int, role: str = "Employee"):
    cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ?", emp_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{role} with EmpId {emp_id} not found")

def validate_project(cursor, project_id: int):
    cursor.execute("SELECT 1 FROM Projects WHERE ProjectId = ?", project_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"ProjectId {project_id} not found")

def validate_company(cursor, company_id: int):
    cursor.execute("SELECT 1 FROM Company WHERE CompanyId = ?", company_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"CompanyId {company_id} not found")

# -------------------------
# CREATE
# -------------------------
@router.post("/project-employees", response_model=Dict[str, str])
def create_project_employee(data: ProjectEmployeeCreate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        validate_emp(cursor, data.EmpId)
        validate_emp(cursor, data.CreatedBy, "CreatedBy")
        validate_project(cursor, data.ProjectId)
        validate_company(cursor, data.CompanyId)
        validate_project_role(cursor, data.ProjectRoleId)

        cursor.execute("""
            INSERT INTO ProjectEmployee (EmpId, ProjectId, CreatedBy, CompanyId, ProjectRoleId, CreatedOn, IsActive)
            VALUES (?, ?, ?, ?, ?, GETDATE(), 1)
        """, data.EmpId, data.ProjectId, data.CreatedBy, data.CompanyId, data.ProjectRoleId)

        db.commit()
        return {"message": "Project employee created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# -------------------------
# UPDATE
# -------------------------
@router.put("/project-employees/{project_employee_id}", response_model=Dict[str, str])
def update_project_employee(project_employee_id: int, data: ProjectEmployeeUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM ProjectEmployee WHERE ProjectEmployeeId = ?", project_employee_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Record not found")

        validate_emp(cursor, data.UpdatedBy, "UpdatedBy")

        fields = []
        params = []

        if data.ProjectId is not None:
            validate_project(cursor, data.ProjectId)
            fields.append("ProjectId = ?")
            params.append(data.ProjectId)

        if data.CompanyId is not None:
            validate_company(cursor, data.CompanyId)
            fields.append("CompanyId = ?")
            params.append(data.CompanyId)

        if data.ProjectRoleId is not None:
            validate_project_role(cursor, data.ProjectRoleId)
            fields.append("ProjectRoleId = ?")
            params.append(data.ProjectRoleId)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = ?")
        params.append(data.UpdatedBy)

        params.append(project_employee_id)

        sql = f"UPDATE ProjectEmployee SET {', '.join(fields)} WHERE ProjectEmployeeId = ?"
        cursor.execute(sql, *params)
        db.commit()

        return {"message": "Project employee updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# -------------------------
# DELETE
# -------------------------
@router.delete("/project-employees/{project_employee_id}", response_model=Dict[str, str])
def delete_project_employee(project_employee_id: int, deleted_by: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM ProjectEmployee WHERE ProjectEmployeeId = ?", project_employee_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Record not found")

        validate_emp(cursor, deleted_by, "DeletedBy")

        cursor.execute("""
            UPDATE ProjectEmployee
            SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ?
            WHERE ProjectEmployeeId = ?
        """, deleted_by, project_employee_id)

        db.commit()
        return {"message": "Project employee soft deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# -------------------------
# LIST
# -------------------------
@router.get("/project-employees", response_model=List[ProjectEmployeeOut])
def list_project_employees(status: str = Query("all", enum=["all", "active", "inactive"]), db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        base_query = """
            SELECT ProjectEmployeeId, EmpId, ProjectId, CreatedOn, CreatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, ProjectRoleId, UpdatedOn, UpdatedBy
            FROM ProjectEmployee
        """
        if status == "active":
            base_query += " WHERE IsActive = 1"
        elif status == "inactive":
            base_query += " WHERE IsActive = 0"

        cursor.execute(base_query)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [ProjectEmployeeOut(**dict(zip(columns, row))) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
@router.get("/project-employees/by-company-project", response_model=List[ProjectEmployeeOut])
def get_project_employees_by_company_and_project(
    company_id: int = Query(..., description="Company ID"),
    project_id: int = Query(..., description="Project ID"),
    status: str = Query("active", enum=["all", "active", "inactive"]),
    db: pyodbc.Connection = Depends(get_connection)
):
    try:
        cursor = db.cursor()

        # Validate existence of company and project
        validate_company(cursor, company_id)
        validate_project(cursor, project_id)

        # Base query
        query = """
            SELECT ProjectEmployeeId, EmpId, ProjectId, CreatedOn, CreatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, ProjectRoleId, UpdatedOn, UpdatedBy
            FROM ProjectEmployee
            WHERE CompanyId = ? AND ProjectId = ?
        """

        params = [company_id, project_id]

        if status == "active":
            query += " AND IsActive = 1"
        elif status == "inactive":
            query += " AND IsActive = 0"

        cursor.execute(query, *params)
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        return [ProjectEmployeeOut(**dict(zip(columns, row))) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
