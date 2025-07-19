from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List, Optional
import pyodbc # Using pyodbc as per your current code
from datetime import datetime
from tables.task import TaskCreate, TaskPaginationRequest, TaskUpdate, TaskOut
from db_connection import get_connection

router = APIRouter()

# Helper validation functions
def validate_user(cursor: pyodbc.Cursor, user_id: int, role: str):
    # Parameters to cursor.execute must be a tuple/list
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", (user_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{role} user not found")

def validate_employee(cursor: pyodbc.Cursor, emp_id: int):
    # Parameters to cursor.execute must be a tuple/list
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", (emp_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Assigned employee not found")

def validate_project(cursor: pyodbc.Cursor, project_id: int):
    # Parameters to cursor.execute must be a tuple/list
    cursor.execute("SELECT 1 FROM [dbo].[Projects] WHERE ProjectId = ?", (project_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

def validate_company(cursor: pyodbc.Cursor, company_id: int):
    # Parameters to cursor.execute must be a tuple/list
    cursor.execute("SELECT 1 FROM [dbo].[company] WHERE CompanyId = ?", (company_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Company not found")

## Task Management Endpoints

### Create Task
@router.post("/tasks", response_model=TaskOut)
def create_task(task: TaskCreate, db: pyodbc.Connection = Depends(get_connection)):
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, 1, ?, ?, ?, ?)
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
            TaskId=row.TaskId,
            Name=row.Name,
            ProjectId=row.ProjectId,
            AssignedTo=row.AssignedTo,
            DocumentPath=row.DocumentPath,
            DocumentUrl=row.DocumentUrl,
            Deadline=row.Deadline,
            Priority=row.Priority,
            Status=row.Status,
            CreatedOn=row.CreatedOn,
            CreatedBy=row.CreatedBy,
            UpdatedOn=row.UpdatedOn,
            UpdatedBy=row.UpdatedBy,
            DeletedOn=row.DeletedOn,
            DeletedBy=row.DeletedBy,
            CompanyId=row.CompanyId,
            Description=row.Description,
            DocumentName=row.DocumentName,
            ExptedHours=row.ExptedHours,
            IsActive=bool(row.IsActive)
        )

    except pyodbc.Error as e: # Catch specific pyodbc errors
        db.rollback() # Rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Update Task
@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Parameters to cursor.execute must be a tuple/list
        cursor.execute("SELECT 1 FROM Task WHERE TaskId = ? AND IsActive = 1", (task_id,))
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
            "IsActive": int(task.IsActive) if task.IsActive is not None else None, # Convert bool to int
            "CompanyId": task.CompanyId
        }

        for key, value in allowed_fields.items():
            if value is not None:
                fields.append(f"{key} = ?")
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No valid fields provided to update.")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = ?")
        params.append(task.UpdatedBy)

        sql = f"UPDATE Task SET {', '.join(fields)} WHERE TaskId = ?"
        # Pass all parameters as a single tuple/list
        cursor.execute(sql, *params, task_id) # Corrected parameter passing for pyodbc
        db.commit()

        # Fetch the updated task to return
        cursor.execute("SELECT * FROM Task WHERE TaskId = ?", (task_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Task not found after update (unexpected error).")

        return TaskOut(
            TaskId=row.TaskId,
            Name=row.Name,
            ProjectId=row.ProjectId,
            AssignedTo=row.AssignedTo,
            DocumentPath=row.DocumentPath,
            DocumentUrl=row.DocumentUrl,
            Deadline=row.Deadline,
            Priority=row.Priority,
            Status=row.Status,
            CreatedOn=row.CreatedOn,
            CreatedBy=row.CreatedBy,
            UpdatedOn=row.UpdatedOn,
            UpdatedBy=row.UpdatedBy,
            DeletedOn=row.DeletedOn,
            DeletedBy=row.DeletedBy,
            CompanyId=row.CompanyId,
            Description=row.Description,
            DocumentName=row.DocumentName,
            ExptedHours=row.ExptedHours,
            IsActive=bool(row.IsActive)
        )

    except pyodbc.Error as e: # Catch specific pyodbc errors
        db.rollback() # Rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


### Delete Task (Soft Delete)
@router.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, deleted_by: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        # Parameters to cursor.execute must be a tuple/list
        cursor.execute("SELECT 1 FROM Task WHERE TaskId = ? AND IsActive = 1", (task_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found or already deleted.")

        validate_user(cursor, deleted_by, "DeletedBy")
        # Parameters to cursor.execute must be a tuple/list
        cursor.execute("""
            UPDATE Task SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? WHERE TaskId = ?
        """, (deleted_by, task_id))
        db.commit()

        return {"message": "Task deleted successfully"}
    except pyodbc.Error as e: # Catch specific pyodbc errors
        db.rollback() # Rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### List All Tasks
@router.get("/alltasks", response_model=List[TaskOut])
def list_tasks(db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM Task WHERE IsActive = 1
        """)
        rows = cursor.fetchall()
        # pyodbc rows often support attribute access directly, so current mapping is fine.
        return [
            TaskOut(
                TaskId=row.TaskId,
                Name=row.Name,
                ProjectId=row.ProjectId,
                AssignedTo=row.AssignedTo,
                DocumentPath=row.DocumentPath,
                DocumentUrl=row.DocumentUrl,
                Deadline=row.Deadline,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description,
                DocumentName=row.DocumentName,
                ExptedHours=row.ExptedHours,
                IsActive=bool(row.IsActive)
            )
            for row in rows
        ]
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
### Tasks by Assigned Employee
@router.get("/tasks/by-assigned/{employee_id}", response_model=List[TaskOut])
def get_tasks_by_assigned_employee(employee_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        # Parameters to cursor.execute must be a tuple/list
        cursor.execute("SELECT * FROM Task WHERE AssignedTo = ? AND IsActive = 1", (employee_id,))
        rows = cursor.fetchall()
        return [
            TaskOut(
                TaskId=row.TaskId,
                Name=row.Name,
                ProjectId=row.ProjectId,
                AssignedTo=row.AssignedTo,
                DocumentPath=row.DocumentPath,
                DocumentUrl=row.DocumentUrl,
                Deadline=row.Deadline,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description,
                DocumentName=row.DocumentName,
                ExptedHours=row.ExptedHours,
                IsActive=bool(row.IsActive)
            )
            for row in rows
        ]
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Tasks by Project Manager
@router.get("/tasks/by-manager/{manager_id}", response_model=List[TaskOut])
def get_tasks_by_project_manager(manager_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        query = """
            SELECT t.* FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE p.ProjectManager = ? AND t.IsActive = 1
        """
        # Parameters to cursor.execute must be a tuple/list
        cursor.execute(query, (manager_id,))
        rows = cursor.fetchall()
        return [
            TaskOut(
                TaskId=row.TaskId,
                Name=row.Name,
                ProjectId=row.ProjectId,
                AssignedTo=row.AssignedTo,
                DocumentPath=row.DocumentPath,
                DocumentUrl=row.DocumentUrl,
                Deadline=row.Deadline,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description,
                DocumentName=row.DocumentName,
                ExptedHours=row.ExptedHours,
                IsActive=bool(row.IsActive)
            )
            for row in rows
        ]
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

### Paginated and Filtered Task Listing
@router.post("/tasks/paginated/filter", response_model=Dict[str, Any])
def get_filtered_paginated_tasks(pagination: TaskPaginationRequest, db: pyodbc.Connection = Depends(get_connection)):
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
            filters.append("p.Name LIKE ?")
            params.append(f"%{project_name}%")
        if task_name:
            filters.append("t.Name LIKE ?")
            params.append(f"%{task_name}%")
        if assigned_to:
            filters.append("t.AssignedTo = ?")
            params.append(assigned_to)
        if priority:
            filters.append("t.Priority = ?")
            params.append(priority)
        if manager_id:
            filters.append("p.ProjectManager = ?")
            params.append(manager_id)

        where_clause = ""
        if filters:
            where_clause = " AND " + " AND ".join(filters)

        with db.cursor() as cursor:
            # Execute count query
            # All parameters must be passed as a single tuple/list
            cursor.execute(count_query_base + where_clause, params)
            total_count_result = cursor.fetchone()
            # Safely get total_count, handling if fetchone() returns None (though unlikely for COUNT(*))
            total_count = total_count_result[0] if total_count_result else 0

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
            fetch_query += " ORDER BY t.Deadline ASC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            # Combine all parameters for the fetch query into one list/tuple
            final_params = params + [offset, PageLimit]
            cursor.execute(fetch_query, final_params)
            rows = cursor.fetchall() # This returns an empty list [] if no rows, which is iterable.

        data = []
        for row in rows:
            # pyodbc row objects typically allow direct attribute access (row.ColumnName)
            # Ensure datetime objects are converted to string if the frontend expects it,
            # or if Pydantic's default JSON encoder has issues.
            # Convert IsActive to boolean
            task_out_item = TaskOut(
                TaskId=row.TaskId,
                Name=row.Name,
                ProjectId=row.ProjectId,
                AssignedTo=row.AssignedTo,
                DocumentPath=row.DocumentPath,
                DocumentUrl=row.DocumentUrl,
                Deadline=row.Deadline,
                Priority=row.Priority,
                Status=row.Status,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description,
                DocumentName=row.DocumentName,
                ExptedHours=row.ExptedHours,
                IsActive=bool(row.IsActive)
            )
            data.append(task_out_item.dict()) # Convert to dict for the overall response

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": PageLimit,
            "total_pages": (total_count + PageLimit - 1) // PageLimit
        }

    except pyodbc.Error as e: # Catch specific pyodbc errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")