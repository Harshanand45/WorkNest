
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict, List
import pyodbc
from db_connection import get_connection
from tables.logtime import LogTimeCreate,LogTimeOut,LogTimeUpdate,PaginationRequest



router = APIRouter()

@router.post("/logtimes", response_model=LogTimeOut)
def create_logtime(logtime: LogTimeCreate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Validate EmpId
        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ?", logtime.EmpId)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="EmpId not found")

        # Validate TaskId
        cursor.execute("SELECT 1 FROM Task WHERE TaskId = ?", logtime.TaskId)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="TaskId not found")

        # Validate CreatedBy
        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ?", logtime.CreatedBy)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="CreatedBy user not found")

        # Validate CompanyId
        cursor.execute("SELECT 1 FROM Company WHERE CompanyId = ?", logtime.CompanyId)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="CompanyId not found")

        insert_query = """
            INSERT INTO LogTime (EmpId, TaskId, Date, CreatedBy, CompanyId, Description, MinutesSpent, HoursSpent)
            OUTPUT INSERTED.LogId, INSERTED.CreatedOn, INSERTED.CreatedBy, INSERTED.IsActive
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query,
                       (logtime.EmpId, logtime.TaskId, logtime.Date, logtime.CreatedBy,
                        logtime.CompanyId, logtime.Description, logtime.MinutesSpent, logtime.HoursSpent))
        inserted = cursor.fetchone()
        db.commit()

        return LogTimeOut(
            LogId=inserted[0],
            CreatedOn=inserted[1],
            CreatedBy=inserted[2],
            IsActive=bool(inserted[3]),
            EmpId=logtime.EmpId,
            TaskId=logtime.TaskId,
            Date=logtime.Date,
            CompanyId=logtime.CompanyId,
            Description=logtime.Description,
            MinutesSpent=logtime.MinutesSpent,
            HoursSpent=logtime.HoursSpent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/logtimes/{log_id}", response_model=dict)
def update_logtime(log_id: int, logtime: LogTimeUpdate, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if LogTime exists and active
        cursor.execute("SELECT 1 FROM LogTime WHERE LogId = ? AND IsActive = 1", log_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="LogTime entry not found")

        # Validate UpdatedBy user
        cursor.execute("SELECT 1 FROM Users WHERE UserId = ?", logtime.UpdatedBy)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="UpdatedBy user not found")

        # Validate EmpId if provided
        if logtime.EmpId is not None:
            cursor.execute("SELECT 1 FROM Employee WHERE EmpId = ?", logtime.EmpId)
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="EmpId not found")

        # Validate TaskId if provided
        if logtime.TaskId is not None:
            cursor.execute("SELECT 1 FROM Task WHERE TaskId = ?", logtime.TaskId)
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="TaskId not found")

        # Prepare update query dynamically
        fields = []
        params = []

        allowed_fields = {
            "EmpId": logtime.EmpId,
            "TaskId": logtime.TaskId,
            "Date": logtime.Date,
            "Description": logtime.Description,
            "MinutesSpent": logtime.MinutesSpent,
            "HoursSpent": logtime.HoursSpent
        }

        for key, value in allowed_fields.items():
            if value is not None:
                fields.append(f"{key} = ?")
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = ?")
        params.append(logtime.UpdatedBy)

        params.append(log_id)

        sql = f"UPDATE LogTime SET {', '.join(fields)} WHERE LogId = ?"
        cursor.execute(sql, *params)
        db.commit()

        return {"message": "LogTime updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/logtimes/{log_id}", response_model=dict)
def delete_logtime(log_id: int, deleted_by: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if LogTime exists and active
        cursor.execute("SELECT 1 FROM LogTime WHERE LogId = ? AND IsActive = 1", log_id)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="LogTime entry not found")

        # Validate deleted_by user
        cursor.execute("SELECT 1 FROM Users WHERE UserId = ?", deleted_by)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="DeletedBy user not found")

        cursor.execute("""
            UPDATE LogTime SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? WHERE LogId = ?
        """, deleted_by, log_id)
        db.commit()

        return {"message": "LogTime deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/alllogtimes", response_model=List[LogTimeOut]) 
def list_logtimes(db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT LogId, EmpId, TaskId, Date, CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, Description, MinutesSpent, HoursSpent
            FROM LogTime
            WHERE IsActive = 1
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append(LogTimeOut(
                LogId=row.LogId,
                EmpId=row.EmpId,
                TaskId=row.TaskId,
                Date=row.Date,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                IsActive=bool(row.IsActive),
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description,
                MinutesSpent=row.MinutesSpent,
                HoursSpent=row.HoursSpent
            ))
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")





@router.post("/logtimesPaginated", response_model=Dict[str, Any])
def get_paginated_logtimes(
    pagination: PaginationRequest,
    db: pyodbc.Connection = Depends(get_connection)
):
    try:
        page = max(pagination.page, 1)
        PageLimit = max(pagination.PageLimit, 1)
        offset = (page - 1) * PageLimit

        cursor = db.cursor()

        # Build filtering conditions
        filters = ["lt.IsActive = 1"]
        params = []

        if pagination.employee_name:
            filters.append("LOWER(e.Name) LIKE ?")
            params.append(f"%{pagination.employee_name.lower()}%")

        if pagination.task_title:
            filters.append("LOWER(t.Title) LIKE ?")
            params.append(f"%{pagination.task_title.lower()}%")

        filter_clause = " AND ".join(filters)

        # Total count query
        count_query = f"""
            SELECT COUNT(*) 
            FROM LogTime lt
            JOIN Employee e ON lt.EmpId = e.EmpId
            JOIN Task t ON lt.TaskId = t.TaskId
            WHERE {filter_clause}
        """
        cursor.execute(count_query, *params)
        total_count = cursor.fetchone()[0]

        # Data query
        data_query = f"""
            SELECT lt.LogId, lt.EmpId, lt.TaskId, lt.Date, lt.CreatedOn, lt.CreatedBy, 
                   lt.UpdatedOn, lt.UpdatedBy, lt.IsActive, lt.DeletedOn, lt.DeletedBy,
                   lt.CompanyId, lt.Description, lt.MinutesSpent, lt.HoursSpent
            FROM LogTime lt
            JOIN Employee e ON lt.EmpId = e.EmpId
            JOIN Task t ON lt.TaskId = t.TaskId
            WHERE {filter_clause}
            ORDER BY lt.LogId
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        cursor.execute(data_query, *params, offset, PageLimit)
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append(LogTimeOut(
                LogId=row.LogId,
                EmpId=row.EmpId,
                TaskId=row.TaskId,
                Date=row.Date,
                CreatedOn=row.CreatedOn,
                CreatedBy=row.CreatedBy,
                UpdatedOn=row.UpdatedOn,
                UpdatedBy=row.UpdatedBy,
                IsActive=bool(row.IsActive),
                DeletedOn=row.DeletedOn,
                DeletedBy=row.DeletedBy,
                CompanyId=row.CompanyId,
                Description=row.Description,
                MinutesSpent=row.MinutesSpent,
                HoursSpent=row.HoursSpent
            ).dict())

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": PageLimit,
            "total_pages": (total_count + PageLimit - 1) // PageLimit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/logtimes/by-task/{task_id}", response_model=List[LogTimeOut])
def get_logs_by_task(task_id: int, db: pyodbc.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT LogId, EmpId, TaskId, Date, CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, Description, MinutesSpent, HoursSpent
            FROM LogTime
            WHERE TaskId = ? AND IsActive = 1
        """, task_id)
        rows = cursor.fetchall()

        return [LogTimeOut(
            LogId=row.LogId,
            EmpId=row.EmpId,
            TaskId=row.TaskId,
            Date=row.Date,
            CreatedOn=row.CreatedOn,
            CreatedBy=row.CreatedBy,
            UpdatedOn=row.UpdatedOn,
            UpdatedBy=row.UpdatedBy,
            IsActive=bool(row.IsActive),
            DeletedOn=row.DeletedOn,
            DeletedBy=row.DeletedBy,
            CompanyId=row.CompanyId,
            Description=row.Description,
            MinutesSpent=row.MinutesSpent,
            HoursSpent=row.HoursSpent
        ) for row in rows]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
