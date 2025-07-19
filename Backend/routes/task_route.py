from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List, Optional
import pymssql # Changed from pyodbc
from datetime import datetime
from tables.task import TaskCreate, TaskPaginationRequest, TaskUpdate, TaskOut
from db_connection import get_connection

router = APIRouter()

# Helper validation functions
def validate_user(cursor, user_id: int, role: str):
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (user_id,)) # Changed ? to %s
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{role} user not found")

def validate_employee(cursor, emp_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (emp_id,)) # Changed ? to %s
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Assigned employee not found")

def validate_project(cursor, project_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[Projects] WHERE ProjectId = %s", (project_id,)) # Changed ? to %s
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

def validate_company(cursor, company_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[company] WHERE CompanyId = %s", (company_id,)) # Changed ? to %s
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Company not found")

# Create Task
@router.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()

        validate_user(cursor, task.CreatedBy, "CreatedBy")
        validate_company(cursor, task.CompanyId)
        validate_project(cursor, task.ProjectId)

        if task.AssignedTo is not None:
            validate_employee(cursor, task.AssignedTo)

        insert_query = """
            INSERT INTO Task
            (Name, ProjectId, AssignedTo, DocumentPath, DocumentUrl, Deadline, Priority, Status,
             CreatedOn, CreatedBy, IsActive, CompanyId, Description, DocumentName, ExptedHours)
            OUTPUT INSERTED.*
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s, 1, %s, %s, %s, %s)
        """ # Changed ? to %s
        cursor.execute(insert_query, ( # Ensured parameters are passed as a tuple
            task.Name, task.ProjectId, task.AssignedTo, task.DocumentPath, task.DocumentUrl,
            task.Deadline, task.Priority, task.Status, task.CreatedBy,
            task.CompanyId, task.Description, task.DocumentName, task.ExptedHours
        ))
        row_data = cursor.fetchone() # Fetches a tuple by default for pymssql
        db.commit()

        if not row_data:
            raise HTTPException(status_code=500, detail="Failed to retrieve inserted task data.")

        # If db_connection.py has as_dict=True, you can use row_data['ColumnName']
        # Otherwise, map tuple indices to fields. Assuming direct column order from OUTPUT INSERTED.*
        # You might need to adjust indices based on your actual table schema
        columns = [col[0] for col in cursor.description]
        row_dict = dict(zip(columns, row_data))

        return TaskOut(
            TaskId=row_dict['TaskId'],
            Name=row_dict['Name'],
            ProjectId=row_dict['ProjectId'],
            AssignedTo=row_dict['AssignedTo'],
            DocumentPath=row_dict['DocumentPath'],
            DocumentUrl=row_dict['DocumentUrl'],
            Deadline=row_dict['Deadline'],
            Priority=row_dict['Priority'],
            Status=row_dict['Status'],
            CreatedOn=row_dict['CreatedOn'],
            CreatedBy=row_dict['CreatedBy'],
            UpdatedOn=row_dict['UpdatedOn'],
            UpdatedBy=row_dict['UpdatedBy'],
            DeletedOn=row_dict['DeletedOn'],
            DeletedBy=row_dict['DeletedBy'],
            CompanyId=row_dict['CompanyId'],
            Description=row_dict['Description'],
            DocumentName=row_dict['DocumentName'],
            ExptedHours=row_dict['ExptedHours'],
            IsActive=bool(row_dict['IsActive'])
        )

    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback() # Rollback changes on error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Ensure rollback for other unexpected errors too
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Update Task
@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Task WHERE TaskId = %s AND IsActive = 1", (task_id,)) # Changed ? to %s
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

        validate_user(cursor, task.UpdatedBy, "UpdatedBy")

        if task.AssignedTo is not None:
            validate_employee(cursor, task.AssignedTo)
        if task.ProjectId is not None:
            validate_project(cursor, task.ProjectId)
        if task.CompanyId is not None:
            validate_company(cursor, task.CompanyId)

        fields = []
        params = []

        allowed_fields = {
            "Name": task.Name,
            "ProjectId": task.ProjectId,
            "AssignedTo": task.AssignedTo,
            "DocumentPath": task.DocumentPath,
            "DocumentUrl": task.DocumentUrl,
            "Deadline": task.Deadline,
            "Priority": task.Priority,
            "Status": task.Status,
            "Description": task.Description,
            "DocumentName": task.DocumentName,
            "ExptedHours": task.ExptedHours,
            "IsActive": int(task.IsActive) if task.IsActive is not None else None,
            "CompanyId": task.CompanyId
        }

        for key, value in allowed_fields.items():
            if value is not None:
                fields.append(f"{key} = %s") # Changed ? to %s
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = %s") # Changed ? to %s
        params.append(task.UpdatedBy)
        params.append(task_id) # Add task_id for the WHERE clause

        sql = f"UPDATE Task SET {', '.join(fields)} WHERE TaskId = %s" # Changed ? to %s
        cursor.execute(sql, tuple(params)) # Ensure params is a tuple
        db.commit()

        cursor.execute("SELECT * FROM Task WHERE TaskId = %s", (task_id,)) # Changed ? to %s
        row_data = cursor.fetchone()

        if not row_data:
            raise HTTPException(status_code=404, detail="Task not found after update (unexpected)")

        # Map tuple indices to fields.
        columns = [col[0] for col in cursor.description]
        row_dict = dict(zip(columns, row_data))

        return TaskOut(
            TaskId=row_dict['TaskId'],
            Name=row_dict['Name'],
            ProjectId=row_dict['ProjectId'],
            AssignedTo=row_dict['AssignedTo'],
            DocumentPath=row_dict['DocumentPath'],
            DocumentUrl=row_dict['DocumentUrl'],
            Deadline=row_dict['Deadline'],
            Priority=row_dict['Priority'],
            Status=row_dict['Status'],
            CreatedOn=row_dict['CreatedOn'],
            CreatedBy=row_dict['CreatedBy'],
            UpdatedOn=row_dict['UpdatedOn'],
            UpdatedBy=row_dict['UpdatedBy'],
            DeletedOn=row_dict['DeletedOn'],
            DeletedBy=row_dict['DeletedBy'],
            CompanyId=row_dict['CompanyId'],
            Description=row_dict['Description'],
            DocumentName=row_dict['DocumentName'],
            ExptedHours=row_dict['ExptedHours'],
            IsActive=bool(row_dict['IsActive'])
        )

    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Delete Task (Soft Delete)
@router.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, deleted_by: int, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM Task WHERE TaskId = %s AND IsActive = 1", (task_id,)) # Changed ? to %s
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

        validate_user(cursor, deleted_by, "DeletedBy")
        cursor.execute("""
            UPDATE Task SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s WHERE TaskId = %s
        """, (deleted_by, task_id)) # Changed ? to %s and ensured tuple
        db.commit()

        return {"message": "Task deleted successfully"}
    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# List All Tasks
@router.get("/alltasks", response_model=List[TaskOut])
def list_tasks(db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM Task WHERE IsActive = 1
        """)
        rows = cursor.fetchall()

        # Get column names from cursor description for dynamic dictionary creation
        columns = [col[0] for col in cursor.description]

        return [
            TaskOut(
                **dict(zip(columns, row)) # Create dict from row and columns
            )
            for row in rows
        ]
    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Tasks by Assigned Employee
@router.get("/tasks/by-assigned/{employee_id}", response_model=List[TaskOut])
def get_tasks_by_assigned_employee(employee_id: int, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Task WHERE AssignedTo = %s AND IsActive = 1", (employee_id,)) # Changed ? to %s
        rows = cursor.fetchall()

        columns = [col[0] for col in cursor.description]

        return [
            TaskOut(
                **dict(zip(columns, row))
            )
            for row in rows
        ]
    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Tasks by Project Manager
@router.get("/tasks/by-manager/{manager_id}", response_model=List[TaskOut])
def get_tasks_by_project_manager(manager_id: int, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        cursor = db.cursor()
        query = """
            SELECT t.* FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE p.ProjectManager = %s AND t.IsActive = 1
        """ # Changed ? to %s
        cursor.execute(query, (manager_id,))
        rows = cursor.fetchall()

        columns = [col[0] for col in cursor.description]

        return [
            TaskOut(
                **dict(zip(columns, row))
            )
            for row in rows
        ]
    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# Paginated and Filtered Task Listing
@router.post("/tasks/paginated/filter", response_model=Dict[str, Any])
def get_filtered_paginated_tasks(pagination: TaskPaginationRequest):
    try:
        page = pagination.page
        PageLimit = pagination.PageLimit
        offset = (page - 1) * PageLimit

        project_name = pagination.ProjectName or ""
        assigned_to = pagination.AssignedTo
        priority = pagination.Priority
        task_name = pagination.TaskName or ""
        manager_id = pagination.ManagerId

        query = """
            SELECT COUNT(*) FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE t.IsActive = 1
        """
        filters = []
        params = []

        if project_name:
            filters.append("p.Name LIKE %s") # Changed ? to %s
            params.append(f"%{project_name}%")
        if task_name:
            filters.append("t.Name LIKE %s") # Changed ? to %s
            params.append(f"%{task_name}%")
        if assigned_to:
            filters.append("t.AssignedTo = %s") # Changed ? to %s
            params.append(assigned_to)
        if priority:
            filters.append("t.Priority = %s") # Changed ? to %s
            params.append(priority)
        if manager_id:
            filters.append("p.ProjectManager = %s") # Changed ? to %s
            params.append(manager_id)

        if filters:
            query += " AND " + " AND ".join(filters)

        with get_connection() as conn: # Connection handled by context manager
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params)) # Ensure params is a tuple
                total_count = cursor.fetchone()[0]

                fetch_query = """
                    SELECT t.* FROM Task t
                    INNER JOIN Projects p ON t.ProjectId = p.ProjectId
                    WHERE t.IsActive = 1
                """
                if filters:
                    fetch_query += " AND " + " AND ".join(filters)

                fetch_query += " ORDER BY t.Deadline ASC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY" # Changed ? to %s
                final_params = params + [offset, PageLimit]
                cursor.execute(fetch_query, tuple(final_params)) # Ensure final_params is a tuple
                rows = cursor.fetchall()

        # Get column names from cursor description for dynamic dictionary creation
        columns = [col[0] for col in cursor.description]

        data = [
            TaskOut(
                **dict(zip(columns, row)) # Create dict from row and columns
            ).dict() # Convert to dict if TaskOut is a Pydantic model
            for row in rows
        ]

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": PageLimit,
            "total_pages": (total_count + PageLimit - 1) // PageLimit
        }

    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")