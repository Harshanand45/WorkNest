from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict, List
import pymssql # Changed from pyodbc/pymysql
from db_connection import get_connection
from tables.logtime import LogTimeCreate, LogTimeOut, LogTimeUpdate, PaginationRequest

router = APIRouter()

@router.post("/logtimes", response_model=LogTimeOut)
def create_logtime(logtime: LogTimeCreate, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Validate EmpId
        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (logtime.EmpId,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="EmpId not found")

        # Validate TaskId
        cursor.execute("SELECT 1 FROM Task WHERE TaskId = %s", (logtime.TaskId,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="TaskId not found")

        # Validate CreatedBy
        # Assuming 'Employee' table is still used for CreatedBy validation as in original
        cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (logtime.CreatedBy,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="CreatedBy user not found")

        # Validate CompanyId
        cursor.execute("SELECT 1 FROM Company WHERE CompanyId = %s", (logtime.CompanyId,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="CompanyId not found")

        insert_query = """
            INSERT INTO LogTime (EmpId, TaskId, Date, CreatedBy, CompanyId, Description, MinutesSpent, HoursSpent)
            OUTPUT INSERTED.LogId, INSERTED.CreatedOn, INSERTED.CreatedBy, INSERTED.IsActive
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query,
                       (logtime.EmpId, logtime.TaskId, logtime.Date, logtime.CreatedBy,
                        logtime.CompanyId, logtime.Description, logtime.MinutesSpent, logtime.HoursSpent))
        inserted = cursor.fetchone()
        db.commit()

        # If using default pymssql cursor (tuples), access by index
        return LogTimeOut(
            LogId=inserted[0],
            CreatedOn=inserted[1],
            CreatedBy=inserted[2],
            IsActive=bool(inserted[3]), # Convert tinyint/bit to boolean
            EmpId=logtime.EmpId,
            TaskId=logtime.TaskId,
            Date=logtime.Date,
            CompanyId=logtime.CompanyId,
            Description=logtime.Description,
            MinutesSpent=logtime.MinutesSpent,
            HoursSpent=logtime.HoursSpent
        )
    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback() # Ensure transaction is rolled back on error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.put("/logtimes/{log_id}", response_model=dict)
def update_logtime(log_id: int, logtime: LogTimeUpdate, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if LogTime exists and active
        cursor.execute("SELECT 1 FROM LogTime WHERE LogId = %s AND IsActive = 1", (log_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="LogTime entry not found or is inactive")

        # Validate UpdatedBy user (assuming 'Users' table based on original code)
        # If UpdatedBy refers to EmployeeId, change 'Users' to 'Employee'
        cursor.execute("SELECT 1 FROM Users WHERE UserId = %s", (logtime.UpdatedBy,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="UpdatedBy user not found")

        # Validate EmpId if provided
        if logtime.EmpId is not None:
            cursor.execute("SELECT 1 FROM Employee WHERE EmpId = %s", (logtime.EmpId,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="EmpId not found")

        # Validate TaskId if provided
        if logtime.TaskId is not None:
            cursor.execute("SELECT 1 FROM Task WHERE TaskId = %s", (logtime.TaskId,))
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
                fields.append(f"{key} = %s")
                params.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        fields.append("UpdatedOn = GETDATE()")
        fields.append("UpdatedBy = %s")
        params.append(logtime.UpdatedBy)

        params.append(log_id) # Add log_id for the WHERE clause

        sql = f"UPDATE LogTime SET {', '.join(fields)} WHERE LogId = %s"
        cursor.execute(sql, tuple(params)) # pymssql expects parameters as a tuple
        db.commit()

        return {"message": "LogTime updated successfully"}

    except pymssql.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.delete("/logtimes/{log_id}", response_model=dict)
def delete_logtime(log_id: int, deleted_by: int = Query(..., description="ID of the user performing the deletion"), db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()

        # Check if LogTime exists and active
        cursor.execute("SELECT 1 FROM LogTime WHERE LogId = %s AND IsActive = 1", (log_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="LogTime entry not found or already inactive")

        # Validate deleted_by user (assuming 'Users' table based on original code)
        # If DeletedBy refers to EmployeeId, change 'Users' to 'Employee'
        cursor.execute("SELECT 1 FROM Users WHERE UserId = %s", (deleted_by,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="DeletedBy user not found")

        cursor.execute("""
            UPDATE LogTime SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s WHERE LogId = %s
        """, (deleted_by, log_id))
        db.commit()

        return {"message": "LogTime deleted successfully"}

    except pymssql.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/alllogtimes", response_model=List[LogTimeOut])
def list_logtimes(db: pymssql.Connection = Depends(get_connection)):
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
            # Accessing by index as default pymssql cursor returns tuples
            result.append(LogTimeOut(
                LogId=row[0],
                EmpId=row[1],
                TaskId=row[2],
                Date=row[3],
                CreatedOn=row[4],
                CreatedBy=row[5],
                UpdatedOn=row[6],
                UpdatedBy=row[7],
                IsActive=bool(row[8]), # Convert tinyint/bit to boolean
                DeletedOn=row[9],
                DeletedBy=row[10],
                CompanyId=row[11],
                Description=row[12],
                MinutesSpent=row[13],
                HoursSpent=row[14]
            ))
        return result

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.post("/logtimesPaginated", response_model=Dict[str, Any])
def get_paginated_logtimes(
    pagination: PaginationRequest,
    db: pymssql.Connection = Depends(get_connection)
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
            filters.append("LOWER(e.Name) LIKE %s")
            params.append(f"%{pagination.employee_name.lower()}%")

        if pagination.task_title:
            filters.append("LOWER(t.Title) LIKE %s")
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
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()[0] # Access first element of the tuple

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
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """
        # params for data_query should include offset and PageLimit
        data_params = params + [offset, PageLimit]
        cursor.execute(data_query, tuple(data_params))
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append(LogTimeOut(
                LogId=row[0],
                EmpId=row[1],
                TaskId=row[2],
                Date=row[3],
                CreatedOn=row[4],
                CreatedBy=row[5],
                UpdatedOn=row[6],
                UpdatedBy=row[7],
                IsActive=bool(row[8]),
                DeletedOn=row[9],
                DeletedBy=row[10],
                CompanyId=row[11],
                Description=row[12],
                MinutesSpent=row[13],
                HoursSpent=row[14]
            ).dict())

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


@router.get("/logtimes/by-task/{task_id}", response_model=List[LogTimeOut])
def get_logs_by_task(task_id: int, db: pymssql.Connection = Depends(get_connection)):
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT LogId, EmpId, TaskId, Date, CreatedOn, CreatedBy, UpdatedOn, UpdatedBy, IsActive,
                   DeletedOn, DeletedBy, CompanyId, Description, MinutesSpent, HoursSpent
            FROM LogTime
            WHERE TaskId = %s AND IsActive = 1
        """, (task_id,))
        rows = cursor.fetchall()

        return [LogTimeOut(
            LogId=row[0],
            EmpId=row[1],
            TaskId=row[2],
            Date=row[3],
            CreatedOn=row[4],
            CreatedBy=row[5],
            UpdatedOn=row[6],
            UpdatedBy=row[7],
            IsActive=bool(row[8]),
            DeletedOn=row[9],
            DeletedBy=row[10],
            CompanyId=row[11],
            Description=row[12],
            MinutesSpent=row[13],
            HoursSpent=row[14]
        ) for row in rows]

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")