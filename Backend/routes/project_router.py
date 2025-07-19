from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List
import pymssql # Changed from pyodbc
from db_connection import get_connection
from tables.project import ProjectCreate, ProjectPaginationRequest, ProjectUpdate, ProjectOut

router = APIRouter()

@router.post("/projects", response_model=dict)
def create_project(proj: ProjectCreate):
    try:
        # Using `get_connection()` as a context manager ensures proper closing
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check for duplicate project name in same company (optional)
                cursor.execute(
                    "SELECT 1 FROM TaskManager.dbo.Projects WHERE Name = %s AND CompanyId = %s AND IsActive = 1",
                    (proj.Name, proj.CompanyId)
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Project with this name already exists in the company.")

                # Validate CreatedBy user exists
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Employee WHERE EmpId = %s", (proj.CreatedBy,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="CreatedBy user not found.")

                # Validate ProjectManager user exists
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Employee WHERE EmpId = %s", (proj.ProjectManager,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="ProjectManager user not found.")

                # Insert project with OUTPUT to get inserted ProjectId
                insert_query = """
                    INSERT INTO TaskManager.dbo.Projects
                    (Name, StartDate, EndDate, ProjectManager, Priority, Status, CreatedOn, CreatedBy, IsActive, CompanyId, Description)
                    OUTPUT INSERTED.ProjectId, INSERTED.CreatedOn, INSERTED.CreatedBy
                    VALUES (%s, %s, %s, %s, %s, %s, GETDATE(), %s, %s, %s, %s)
                """
                cursor.execute(
                    insert_query,
                    (proj.Name, proj.StartDate, proj.EndDate, proj.ProjectManager, proj.Priority,
                     proj.Status, proj.CreatedBy, int(proj.IsActive), proj.CompanyId, proj.Description)
                )
                inserted_row = cursor.fetchone()
                conn.commit()

    except pymssql.Error as e: # Catch pymssql specific errors
        # No rollback needed here if using `with conn:` context for `get_connection`
        # and cursor also within `with` as `pymssql` handles implicit transaction for DML.
        # However, explicit rollback on error is safer if you modify transaction behavior.
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Assuming inserted_row will always be available if no exception occurred
    # Accessing by index as default pymssql cursor returns tuples
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
def update_project(project_id: int, project: ProjectUpdate, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if project exists and is active
        cursor.execute("SELECT 1 FROM Projects WHERE ProjectId = %s AND IsActive = 1", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found or is inactive")

        # Validate UpdatedBy user
        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (project.UpdatedBy,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="UpdatedBy user not found.")

        # If ProjectManager is being updated, validate it
        if project.ProjectManager is not None:
            cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (project.ProjectManager,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="ProjectManager user not found.")

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
                fields.append(f"{key} = %s")
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Add UpdatedOn and UpdatedBy
        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = %s")
        params.append(project.UpdatedBy)

        params.append(project_id) # Add project_id for the WHERE clause

        sql = f"UPDATE Projects SET {', '.join(fields)} WHERE ProjectId = %s"
        cursor.execute(sql, tuple(params)) # pymssql expects parameters as a tuple
        db.commit()

        return {"message": "Project updated successfully"}

    except pymssql.Error as e:
        db.rollback() # Rollback changes on error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.delete("/projects/{project_id}", response_model=dict)
def delete_project(project_id: int, deleted_by: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if project exists and is active
        cursor.execute("SELECT 1 FROM Projects WHERE ProjectId = %s AND IsActive = 1", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found or is already inactive")

        # Validate deleted_by user
        cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (deleted_by,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="DeletedBy user not found.")

        cursor.execute("""
            UPDATE Projects SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s WHERE ProjectId = %s
        """, (deleted_by, project_id))
        db.commit()

        return {"message": "Project deleted successfully"}

    except pymssql.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/allprojects", response_model=List[ProjectOut])
def list_projects(db: pymssql.Connection = Depends(get_connection)):
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
            # Accessing by index as default pymssql cursor returns tuples
            result.append(ProjectOut(
                ProjectId=row[0],
                Name=row[1],
                StartDate=row[2],
                EndDate=row[3],
                ProjectManager=row[4],
                Priority=row[5],
                Status=row[6],
                CreatedOn=row[7],
                CreatedBy=row[8],
                UpdatedOn=row[9],
                UpdatedBy=row[10],
                IsActive=bool(row[11]), # Convert tinyint/bit to boolean
                DeletedOn=row[12],
                DeletedBy=row[13],
                CompanyId=row[14],
                Description=row[15]
            ))
        return result

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


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
            filters.append("Name LIKE %s")
            params.append(f"%{pagination.name}%")

        if pagination.status:
            filters.append("Status = %s")
            params.append(pagination.status)

        if pagination.priority:
            filters.append("Priority = %s")
            params.append(pagination.priority)

        if pagination.project_manager is not None:
            filters.append("ProjectManager = %s")
            params.append(pagination.project_manager)

        where_clause = " AND ".join(filters)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Count total matching projects
                cursor.execute(f"SELECT COUNT(*) FROM Projects WHERE {where_clause}", tuple(params))
                total_count = cursor.fetchone()[0] # Access first element of the tuple

                # Fetch paginated projects
                cursor.execute(f"""
                    SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                           CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                           DeletedOn, DeletedBy, CompanyId, Description
                    FROM Projects
                    WHERE {where_clause}
                    ORDER BY ProjectId DESC
                    OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """, tuple(params + [offset, PageLimit])) # Combine params for WHERE and OFFSET/FETCH

                rows = cursor.fetchall()

        data = [
            ProjectOut(
                ProjectId=row[0],
                Name=row[1],
                StartDate=row[2].strftime("%Y-%m-%d") if isinstance(row[2], datetime) else None,
                EndDate=row[3].strftime("%Y-%m-%d") if isinstance(row[3], datetime) else None,
                ProjectManager=row[4],
                Priority=row[5],
                Status=row[6],
                CreatedOn=row[7].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[7], datetime) else None,
                CreatedBy=row[8],
                UpdatedOn=row[9].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[9], datetime) else None,
                UpdatedBy=row[10],
                IsActive=bool(row[11]),
                DeletedOn=row[12].strftime("%Y-%m-%d %H:%M:%S") if row[12] and isinstance(row[12], datetime) else None,
                DeletedBy=row[13],
                CompanyId=row[14],
                Description=row[15]
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

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/projects/by-manager", response_model=List[ProjectOut])
def get_projects_by_manager(emp_id: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                   CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive, DeletedOn, DeletedBy, CompanyId, Description
            FROM Projects
            WHERE IsActive = 1 AND ProjectManager = %s
        """, (emp_id,))

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(ProjectOut(
                ProjectId=row[0],
                Name=row[1],
                StartDate=row[2].strftime("%Y-%m-%d") if isinstance(row[2], datetime) else None,
                EndDate=row[3].strftime("%Y-%m-%d") if isinstance(row[3], datetime) else None,
                ProjectManager=row[4],
                Priority=row[5],
                Status=row[6],
                CreatedOn=row[7].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[7], datetime) else None,
                CreatedBy=row[8],
                UpdatedOn=row[9].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[9], datetime) else None,
                UpdatedBy=row[10],
                IsActive=bool(row[11]),
                DeletedOn=row[12].strftime("%Y-%m-%d %H:%M:%S") if row[12] and isinstance(row[12], datetime) else None,
                DeletedBy=row[13],
                CompanyId=row[14],
                Description=row[15]
            ))
        return result

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project_by_id(project_id: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT ProjectId, Name, StartDate, EndDate, ProjectManager, Priority, Status,
                   CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, Description
            FROM Projects
            WHERE ProjectId = %s AND IsActive = 1
        """, (project_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found.")

        return ProjectOut(
            ProjectId=row[0],
            Name=row[1],
            StartDate=row[2].strftime("%Y-%m-%d") if isinstance(row[2], datetime) else None,
            EndDate=row[3].strftime("%Y-%m-%d") if isinstance(row[3], datetime) else None,
            ProjectManager=row[4],
            Priority=row[5],
            Status=row[6],
            CreatedOn=row[7].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[7], datetime) else None,
            CreatedBy=row[8],
            UpdatedOn=row[9].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[9], datetime) else None,
            UpdatedBy=row[10],
            IsActive=bool(row[11]),
            DeletedOn=row[12].strftime("%Y-%m-%d %H:%M:%S") if row[12] and isinstance(row[12], datetime) else None,
            DeletedBy=row[13],
            CompanyId=row[14],
            Description=row[15]
        )

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")