from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List, Optional
import pymssql # Changed from pyodbc
from datetime import datetime
from tables.task import TaskCreate, TaskPaginationRequest, TaskUpdate, TaskOut
from db_connection import get_connection

router = APIRouter()

# Helper validation functions - changed to pymssql parameter style and cursor type
def validate_user(cursor: pymssql.Cursor, user_id: int, role: str):
    # Use %s placeholder and pass parameters as a tuple
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{role} user not found")

def validate_employee(cursor: pymssql.Cursor, emp_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = %s", (emp_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Assigned employee not found")

def validate_project(cursor: pymssql.Cursor, project_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[Projects] WHERE ProjectId = %s", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

def validate_company(cursor: pymssql.Cursor, company_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[company] WHERE CompanyId = %s", (company_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Company not found")

## Task Management Endpoints

### Create Task
@router.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: pymssql.Connection = Depends(get_connection)):
    try:
        # Create cursor with as_dict=True for dictionary-like row access
        cursor = db.cursor(as_dict=True)

        validate_user(cursor, task.CreatedBy, "CreatedBy")
        validate_company(cursor, task.CompanyId)
        validate_project(cursor, task.ProjectId)

        if task.AssignedTo is not None:
            validate_employee(cursor, task.AssignedTo)

        insert_query = """
            INSERT INTO Task
            (Name, ProjectId, AssignedTo, DocumentPath, DocumentUrl, Deadline, Priority, Status,
             CreatedOn, CreatedBy, IsActive, CompanyId, Description, DocumentName, ExptedHours)
            OUTPUT INSERTED.* -- SQL Server specific, works with pymssql
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, GETDATE(), %s, 1, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            task.Name, task.ProjectId, task.AssignedTo, task.DocumentPath, task.DocumentUrl,
            task.Deadline, task.Priority, task.Status, task.CreatedBy,
            task.CompanyId, task.Description, task.DocumentName, task.ExptedHours
        ))
        row = cursor.fetchone()
        db.commit()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to retrieve inserted task data after creation.")

        return TaskOut(
            TaskId=row['TaskId'], # Access as dictionary key
            Name=row['Name'],
            ProjectId=row['ProjectId'],
            AssignedTo=row['AssignedTo'],
            DocumentPath=row['DocumentPath'],
            DocumentUrl=row['DocumentUrl'],
            Deadline=row['Deadline'],
            Priority=row['Priority'],
            Status=row['Status'],
            CreatedOn=row['CreatedOn'],
            CreatedBy=row['CreatedBy'],
            UpdatedOn=row['UpdatedOn'],
            UpdatedBy=row['UpdatedBy'],
            DeletedOn=row['DeletedOn'],
            DeletedBy=row['DeletedBy'],
            CompanyId=row['CompanyId'],
            Description=row['Description'],
            DocumentName=row['DocumentName'],
            ExptedHours=row['ExptedHours'],
            IsActive=bool(row['IsActive']) # Convert 1/0 to bool
        )

    except pymssql.Error as e: # Catch specific pymssql errors
        db.rollback() # Rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Update Task
@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor(as_dict=True) # Create cursor with as_dict=True

        cursor.execute("SELECT 1 FROM Task WHERE TaskId = %s AND IsActive = 1", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found or is inactive.")

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
            "IsActive": int(task.IsActive) if task.IsActive is not None else None, # Convert bool to int for SQL Server BIT/TINYINT
            "CompanyId": task.CompanyId
        }

        for key, value in allowed_fields.items():
            if value is not None:
                fields.append(f"{key} = %s") # pymssql placeholder
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No valid fields provided to update.")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = %s") # pymssql placeholder
        params.append(task.UpdatedBy)

        sql = f"UPDATE Task SET {', '.join(fields)} WHERE TaskId = %s" # pymssql placeholder
        
        # All parameters must be passed as a single tuple/list
        final_params = tuple(params) + (task_id,) 
        cursor.execute(sql, final_params)
        db.commit()

        # Fetch the updated task to return
        cursor.execute("SELECT * FROM Task WHERE TaskId = %s", (task_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Task not found after update (unexpected error).")

        return TaskOut(
            TaskId=row['TaskId'],
            Name=row['Name'],
            ProjectId=row['ProjectId'],
            AssignedTo=row['AssignedTo'],
            DocumentPath=row['DocumentPath'],
            DocumentUrl=row['DocumentUrl'],
            Deadline=row['Deadline'],
            Priority=row['Priority'],
            Status=row['Status'],
            CreatedOn=row['CreatedOn'],
            CreatedBy=row['CreatedBy'],
            UpdatedOn=row['UpdatedOn'],
            UpdatedBy=row['UpdatedBy'],
            DeletedOn=row['DeletedOn'],
            DeletedBy=row['DeletedBy'],
            CompanyId=row['CompanyId'],
            Description=row['Description'],
            DocumentName=row['DocumentName'],
            ExptedHours=row['ExptedHours'],
            IsActive=bool(row['IsActive'])
        )

    except pymssql.Error as e: # Catch specific pymssql errors
        db.rollback() # Rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


### Delete Task (Soft Delete)
@router.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, deleted_by: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor() # Dictionary cursor not strictly needed here, but fine

        cursor.execute("SELECT 1 FROM Task WHERE TaskId = %s AND IsActive = 1", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found or already deleted.")

        validate_user(cursor, deleted_by, "DeletedBy")
        cursor.execute("""
            UPDATE Task SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s WHERE TaskId = %s
        """, (deleted_by, task_id)) # Pass parameters as a single tuple
        db.commit()

        return {"message": "Task deleted successfully"}
    except pymssql.Error as e: # Catch specific pymssql errors
        db.rollback() # Rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### List All Tasks
@router.get("/alltasks", response_model=List[TaskOut])
def list_tasks(db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor(as_dict=True) # Create cursor with as_dict=True
        cursor.execute("""
            SELECT * FROM Task WHERE IsActive = 1
        """)
        rows = cursor.fetchall() # Returns list of dicts

        return [
            TaskOut(
                TaskId=row['TaskId'],
                Name=row['Name'],
                ProjectId=row['ProjectId'],
                AssignedTo=row['AssignedTo'],
                DocumentPath=row['DocumentPath'],
                DocumentUrl=row['DocumentUrl'],
                Deadline=row['Deadline'],
                Priority=row['Priority'],
                Status=row['Status'],
                CreatedOn=row['CreatedOn'],
                CreatedBy=row['CreatedBy'],
                UpdatedOn=row['UpdatedOn'],
                UpdatedBy=row['UpdatedBy'],
                DeletedOn=row['DeletedOn'],
                DeletedBy=row['DeletedBy'],
                CompanyId=row['CompanyId'],
                Description=row['Description'],
                DocumentName=row['DocumentName'],
                ExptedHours=row['ExptedHours'],
                IsActive=bool(row['IsActive'])
            )
            for row in rows
        ]
    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Tasks by Assigned Employee
@router.get("/tasks/by-assigned/{employee_id}", response_model=List[TaskOut])
def get_tasks_by_assigned_employee(employee_id: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor(as_dict=True) # Create cursor with as_dict=True
        cursor.execute("SELECT * FROM Task WHERE AssignedTo = %s AND IsActive = 1", (employee_id,))
        rows = cursor.fetchall()
        return [
            TaskOut(
                TaskId=row['TaskId'],
                Name=row['Name'],
                ProjectId=row['ProjectId'],
                AssignedTo=row['AssignedTo'],
                DocumentPath=row['DocumentPath'],
                DocumentUrl=row['DocumentUrl'],
                Deadline=row['Deadline'],
                Priority=row['Priority'],
                Status=row['Status'],
                CreatedOn=row['CreatedOn'],
                CreatedBy=row['CreatedBy'],
                UpdatedOn=row['UpdatedOn'],
                UpdatedBy=row['UpdatedBy'],
                DeletedOn=row['DeletedOn'],
                DeletedBy=row['DeletedBy'],
                CompanyId=row['CompanyId'],
                Description=row['Description'],
                DocumentName=row['DocumentName'],
                ExptedHours=row['ExptedHours'],
                IsActive=bool(row['IsActive'])
            )
            for row in rows
        ]
    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Tasks by Project Manager
@router.get("/tasks/by-manager/{manager_id}", response_model=List[TaskOut])
def get_tasks_by_project_manager(manager_id: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor(as_dict=True) # Create cursor with as_dict=True
        query = """
            SELECT t.* FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE p.ProjectManager = %s AND t.IsActive = 1
        """
        cursor.execute(query, (manager_id,))
        rows = cursor.fetchall()
        return [
            TaskOut(
                TaskId=row['TaskId'],
                Name=row['Name'],
                ProjectId=row['ProjectId'],
                AssignedTo=row['AssignedTo'],
                DocumentPath=row['DocumentPath'],
                DocumentUrl=row['DocumentUrl'],
                Deadline=row['Deadline'],
                Priority=row['Priority'],
                Status=row['Status'],
                CreatedOn=row['CreatedOn'],
                CreatedBy=row['CreatedBy'],
                UpdatedOn=row['UpdatedOn'],
                UpdatedBy=row['UpdatedBy'],
                DeletedOn=row['DeletedOn'],
                DeletedBy=row['DeletedBy'],
                CompanyId=row['CompanyId'],
                Description=row['Description'],
                DocumentName=row['DocumentName'],
                ExptedHours=row['ExptedHours'],
                IsActive=bool(row['IsActive'])
            )
            for row in rows
        ]
    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Paginated and Filtered Task Listing
@router.post("/tasks/paginated/filter", response_model=Dict[str, Any])
def get_filtered_paginated_tasks(pagination: TaskPaginationRequest, db: pymssql.Connection = Depends(get_connection)):
    try:
        page = pagination.page
        PageLimit = pagination.PageLimit
        offset = (page - 1) * PageLimit

        project_name = pagination.ProjectName or ""
        assigned_to = pagination.AssignedTo
        priority = pagination.Priority
        task_name = pagination.TaskName or ""
        manager_id = pagination.ManagerId

        # Base query for counting
        count_query_base = """
            SELECT COUNT(*) FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE t.IsActive = 1
        """
        # Base query for fetching data
        fetch_query_base = """
            SELECT t.* FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE t.IsActive = 1
        """

        filters = []
        params = []

        if project_name:
            filters.append("p.Name LIKE %s") # pymssql LIKE placeholder
            params.append(f"%{project_name}%")
        if task_name:
            filters.append("t.Name LIKE %s") # pymssql LIKE placeholder
            params.append(f"%{task_name}%")
        if assigned_to:
            filters.append("t.AssignedTo = %s") # pymssql placeholder
            params.append(assigned_to)
        if priority:
            filters.append("t.Priority = %s") # pymssql placeholder
            params.append(priority)
        if manager_id:
            filters.append("p.ProjectManager = %s") # pymssql placeholder
            params.append(manager_id)

        where_clause = ""
        if filters:
            where_clause = " AND " + " AND ".join(filters)

        with db.cursor(as_dict=True) as cursor: # Create cursor with as_dict=True
            # Execute count query
            cursor.execute(count_query_base + where_clause, tuple(params)) # Pass parameters as a tuple
            total_count_result = cursor.fetchone()
            total_count = total_count_result[''] if total_count_result else 0 # COUNT(*) result is often an empty string key in dicts

            if total_count == 0:
                return {
                    "data": [],
                    "total": 0,
                    "page": page,
                    "PageLimit": PageLimit,
                    "total_pages": 0
                }

            # Execute fetch query
            fetch_query = fetch_query_base + where_clause
            # SQL Server OFFSET/FETCH NEXT syntax remains the same
            fetch_query += " ORDER BY t.Deadline ASC OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
            
            # Combine all parameters for the fetch query into one tuple
            final_params = tuple(params) + (offset, PageLimit)
            
            cursor.execute(fetch_query, final_params)
            rows = cursor.fetchall() # Returns list of dicts

        data = []
        for row in rows:
            task_out_item = TaskOut(
                TaskId=row['TaskId'],
                Name=row['Name'],
                ProjectId=row['ProjectId'],
                AssignedTo=row['AssignedTo'],
                DocumentPath=row['DocumentPath'],
                DocumentUrl=row['DocumentUrl'],
                Deadline=row['Deadline'],
                Priority=row['Priority'],
                Status=row['Status'],
                CreatedOn=row['CreatedOn'],
                CreatedBy=row['CreatedBy'],
                UpdatedOn=row['UpdatedOn'],
                UpdatedBy=row['UpdatedBy'],
                DeletedOn=row['DeletedOn'],
                DeletedBy=row['DeletedBy'],
                CompanyId=row['CompanyId'],
                Description=row['Description'],
                DocumentName=row['DocumentName'],
                ExptedHours=row['ExptedHours'],
                IsActive=bool(row['IsActive'])
            )
            data.append(task_out_item.dict())

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": PageLimit,
            "total_pages": (total_count + PageLimit - 1) // PageLimit
        }

    except pymssql.Error as e: # Catch specific pymssql errors
        # Include more detail in the error message for debugging SQL errors
        # Note: fetch_query and final_params might not be defined if error occurs early
        error_detail = f"Database error: {str(e)}"
        if 'fetch_query' in locals() and 'final_params' in locals():
             error_detail += f". Query might be: {fetch_query} with parameters: {final_params}"
        raise HTTPException(status_code=500, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")