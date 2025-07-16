from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List
import pyodbc
from db_connection import get_connection
from tables.project import ProjectCreate, ProjectPaginationRequest, ProjectUpdate, ProjectOut

router = APIRouter()

@router.post("/projects", response_model=dict)

def create_project(proj: ProjectCreate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check for duplicate project name in same company (optional)
                cursor.execute(
                    "SELECT 1 FROM TaskManager.dbo.Projects WHERE Name = ? AND CompanyId = ? AND IsActive = 1",
                    (proj.Name, proj.CompanyId)
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Project with this name already exists in the company.")

                # Validate CreatedBy user exists
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Employee WHERE EmpId = ?", (proj.CreatedBy,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="CreatedBy user not found.")

                # Validate ProjectManager user exists
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Employee WHERE EmpId = ?", (proj.ProjectManager,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="ProjectManager user not found.")

                # Insert project with OUTPUT to get inserted ProjectId
                insert_query = """
                    INSERT INTO TaskManager.dbo.Projects
                    (Name, StartDate, EndDate, ProjectManager, Priority, Status, CreatedOn, CreatedBy, IsActive, CompanyId, Description)
                    OUTPUT INSERTED.ProjectId, INSERTED.CreatedOn, INSERTED.CreatedBy
                    VALUES (?, ?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?)
                """
                cursor.execute(
                    insert_query,
                    (proj.Name, proj.StartDate, proj.EndDate, proj.ProjectManager, proj.Priority,
                     proj.Status, proj.CreatedBy, int(proj.IsActive), proj.CompanyId, proj.Description)
                )
                inserted_row = cursor.fetchone()
                conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "project_id": inserted_row[0],
        "created_on": inserted_row[1].strftime("%Y-%m-%d %H:%M:%S") if inserted_row[1] else None,
        "created_by": inserted_row[2],
        "name": proj.Name,
        "start_date": proj.StartDate,
        "end_date": proj.EndDate,
        "project_manager": proj.ProjectManager,
        "priority": proj.Priority,
        "status": proj.Status,
        "company_id": proj.CompanyId,
        "description": proj.Description,
        "is_active": proj.IsActive
    }

@router.put("/projects/{project_id}", response_model=dict)
def update_project(project_id: int, project: ProjectUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if project exists and is active
        cursor.execute("SELECT 1 FROM Projects WHERE ProjectId = ? AND IsActive = 1", project_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate UpdatedBy user
        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", project.UpdatedBy)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="UpdatedBy user not found")

        # If ProjectManager is being updated, validate it
        if project.ProjectManager is not None:
            cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", project.ProjectManager)
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="ProjectManager user not found")

        # Build update statement dynamically
        fields = []
        params = []

        allowed_fields = {
            "Name": project.Name,
            "StartDate": project.StartDate,
            "EndDate": project.EndDate,
            "ProjectManager": project.ProjectManager,
            "Priority": project.Priority,
            "Status": project.Status,
            "Description": project.Description,
            "IsActive": project.IsActive
        }

        for key, value in allowed_fields.items():
            if value is not None:
                fields.append(f"{key} = ?")
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add UpdatedOn and UpdatedBy
        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = ?")
        params.append(project.UpdatedBy)

        params.append(project_id)

        sql = f"UPDATE Projects SET {', '.join(fields)} WHERE ProjectId = ?"
        cursor.execute(sql, *params)
        db.commit()

        return {"message": "Project updated successfully"}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.delete("/projects/{project_id}", response_model=dict)
def delete_project(project_id: int, deleted_by: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if project exists and is active
        cursor.execute("SELECT 1 FROM Projects WHERE ProjectId = ? AND IsActive = 1", project_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate deleted_by user
        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", deleted_by)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="DeletedBy user not found")

        cursor.execute("""
            UPDATE Projects SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? WHERE ProjectId = ?
        """, deleted_by, project_id)
        db.commit()

        return {"message": "Project deleted successfully"}

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/allprojects", response_model=List[ProjectOut])
def list_projects(db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                   CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive, DeletedOn, DeletedBy, CompanyId, Description
            FROM Projects
            WHERE IsActive = 1
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(ProjectOut(
                ProjectId=row.ProjectId,
                Name=row.Name,
                StartDate=row.StartDate,
                EndDate=row.EndDate,
                ProjectManager=row.ProjectManager,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                IsActive=bool(row.IsActive),
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description
            ))
        return result

    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.post("/projects/paginated", response_model=Dict[str, Any])
def get_paginated_projects(pagination: ProjectPaginationRequest):
    try:
        page = pagination.page
        PageLimit = pagination.PageLimit
        offset = (page - 1) * PageLimit

        filters = ["IsActive = 1"]
        params = []

        # Apply filters
        if pagination.name:
            filters.append("Name LIKE ?")
            params.append(f"%{pagination.name}%")

        if pagination.status:
            filters.append("Status = ?")
            params.append(pagination.status)

        if pagination.priority:
            filters.append("Priority = ?")
            params.append(pagination.priority)

        if pagination.project_manager is not None:
            filters.append("ProjectManager = ?")
            params.append(pagination.project_manager)

        where_clause = " AND ".join(filters)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Count total matching projects
                cursor.execute(f"SELECT COUNT(*) FROM Projects WHERE {where_clause}", params)
                total_count = cursor.fetchone()[0]

                # Fetch paginated projects
                cursor.execute(f"""
                    SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                           CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                           DeletedOn, DeletedBy, CompanyId, Description
                    FROM Projects
                    WHERE {where_clause}
                    ORDER BY ProjectId DESC
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """, params + [offset, PageLimit])

                rows = cursor.fetchall()

        data = [
            ProjectOut(
                ProjectId=row.ProjectId,
                Name=row.Name,
                StartDate=row.StartDate.strftime("%Y-%m-%d") if isinstance(row.StartDate, datetime) else None,
                EndDate=row.EndDate.strftime("%Y-%m-%d") if isinstance(row.EndDate, datetime) else None,
                ProjectManager=row.ProjectManager,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.CreatedOn, datetime) else None,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.UpdatedOn, datetime) else None,
                UpdatedBy=row.UpdatedBy,
                IsActive=bool(row.IsActive),
                DeletedOn=row.DeletedOn.strftime("%Y-%m-%d %H:%M:%S") if row.DeletedOn and isinstance(row.DeletedOn, datetime) else None,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description
            ).dict()
            for row in rows
        ]

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": PageLimit,
            "total_pages": (total_count + PageLimit - 1) // PageLimit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/projects/by-manager", response_model=List[ProjectOut])
def get_projects_by_manager(emp_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                   CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive, DeletedOn, DeletedBy, CompanyId, Description
            FROM Projects
            WHERE IsActive = 1 AND ProjectManager = ?
        """, emp_id)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(ProjectOut(
                ProjectId=row.ProjectId,
                Name=row.Name,
                StartDate=row.StartDate.strftime("%Y-%m-%d") if isinstance(row.StartDate, datetime) else None,
                EndDate=row.EndDate.strftime("%Y-%m-%d") if isinstance(row.EndDate, datetime) else None,
                ProjectManager=row.ProjectManager,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.CreatedOn, datetime) else None,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.UpdatedOn, datetime) else None,
                UpdatedBy=row.UpdatedBy,
                IsActive=bool(row.IsActive),
                DeletedOn=row.DeletedOn.strftime("%Y-%m-%d %H:%M:%S") if row.DeletedOn and isinstance(row.DeletedOn, datetime) else None,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description
            ))
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project_by_id(project_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                   CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, Description
            FROM Projects
            WHERE ProjectId = ? AND IsActive = 1
        """, project_id)

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        return ProjectOut(
            ProjectId=row.ProjectId,
            Name=row.Name,
            StartDate=row.StartDate.strftime("%Y-%m-%d") if isinstance(row.StartDate, datetime) else None,
            EndDate=row.EndDate.strftime("%Y-%m-%d") if isinstance(row.EndDate, datetime) else None,
            ProjectManager=row.ProjectManager,
            Priority=row.Priority,
            Status=row.Status,
            CreatedOn=row.CreatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.CreatedOn, datetime) else None,
            CreatedBy=row.CreatedBy,
            UpdatedOn=row.UpdatedOn.strftime("%Y-%m-%d %H:%M:%S") if isinstance(row.UpdatedOn, datetime) else None,
            UpdatedBy=row.UpdatedBy,
            IsActive=bool(row.IsActive),
            DeletedOn=row.DeletedOn.strftime("%Y-%m-%d %H:%M:%S") if row.DeletedOn and isinstance(row.DeletedOn, datetime) else None,
            DeletedBy=row.DeletedBy,
            CompanyId=row.CompanyId,
            Description=row.Description
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
