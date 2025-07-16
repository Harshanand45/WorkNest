from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict, List, Optional
import pyodbc
from datetime import datetime
from tables.task import TaskCreate, TaskPaginationRequest, TaskUpdate, TaskOut
from db_connection import get_connection

router = APIRouter()

# Helper validation functions
def validate_user(cursor, user_id: int, role: str):
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", user_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"{role} user not found")

def validate_employee(cursor, emp_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[Employee] WHERE EmpId = ?", emp_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Assigned employee not found")

def validate_project(cursor, project_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[Projects] WHERE ProjectId = ?", project_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Project not found")

def validate_company(cursor, company_id: int):
    cursor.execute("SELECT 1 FROM [dbo].[company] WHERE CompanyId = ?", company_id)
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Company not found")

# Create Task
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Update Task
@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: TaskUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Task WHERE TaskId = ? AND IsActive = 1", task_id)
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
                fields.append(f"{key} = ?")
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = ?")
        params.append(task.UpdatedBy)
        params.append(task_id)

        sql = f"UPDATE Task SET {', '.join(fields)} WHERE TaskId = ?"
        cursor.execute(sql, *params)
        db.commit()

        cursor.execute("SELECT * FROM Task WHERE TaskId = ?", task_id)
        row = cursor.fetchone()
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Delete Task (Soft Delete)
@router.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: int, deleted_by: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM Task WHERE TaskId = ? AND IsActive = 1", task_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Task not found")

        validate_user(cursor, deleted_by, "DeletedBy")
        cursor.execute("""
            UPDATE Task SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? WHERE TaskId = ?
        """, deleted_by, task_id)
        db.commit()

        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# List All Tasks
@router.get("/alltasks", response_model=List[TaskOut])
def list_tasks(db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM Task WHERE IsActive = 1
        """)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Tasks by Assigned Employee
@router.get("/tasks/by-assigned/{employee_id}", response_model=List[TaskOut])
def get_tasks_by_assigned_employee(employee_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM Task WHERE AssignedTo = ? AND IsActive = 1", employee_id)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Tasks by Project Manager
@router.get("/tasks/by-manager/{manager_id}", response_model=List[TaskOut])
def get_tasks_by_project_manager(manager_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        query = """
            SELECT t.* FROM Task t
            INNER JOIN Projects p ON t.ProjectId = p.ProjectId
            WHERE p.ProjectManager = ? AND t.IsActive = 1
        """
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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

        if filters:
            query += " AND " + " AND ".join(filters)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                total_count = cursor.fetchone()[0]

                fetch_query = """
                    SELECT t.* FROM Task t
                    INNER JOIN Projects p ON t.ProjectId = p.ProjectId
                    WHERE t.IsActive = 1
                """
                if filters:
                    fetch_query += " AND " + " AND ".join(filters)

                fetch_query += " ORDER BY t.Deadline ASC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
                final_params = params + [offset, PageLimit]
                cursor.execute(fetch_query, final_params)
                rows = cursor.fetchall()

        data = [
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
