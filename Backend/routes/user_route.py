from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from tables.users import User, UserCreate, UserUpdate,UserPaginationRequest
from db_connection import get_connection
from datetime import datetime
from tables.auth import get_current_user
from fastapi import Depends

router = APIRouter()

# Helper to validate if a user_id exists
def check_user_exists(user_id: int, cursor) -> bool:
    cursor.execute("SELECT EmpId FROM TaskManager.dbo.Employee WHERE EmpId = ?", (user_id,))
    return cursor.fetchone() is not None



# ✅ Create a new user with user existence validation
@router.post("/users", response_model=User)
def create_user(user: UserCreate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if email exists
                cursor.execute("SELECT COUNT(*) FROM TaskManager.dbo.Users WHERE Email = ?", (user.email,))
                if cursor.fetchone()[0] > 0:
                    raise HTTPException(status_code=400, detail="Email already exists.")

                # Check if created_by user exists
                if not check_user_exists(user.created_by, cursor):
                    raise HTTPException(status_code=400, detail=f"CreatedBy user ID {user.created_by} not found.")

                cursor.execute(
                    "INSERT INTO TaskManager.dbo.Users "
                    "(Email, Password, IsActive, CreatedBy, RoleId, CompanyId) "
                    "OUTPUT INSERTED.UserId, INSERTED.CreatedOn, INSERTED.CreatedBy "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (user.email, user.password, int(user.is_active), user.created_by, user.role_id, user.company_id)
                )
                inserted_row = cursor.fetchone()
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "user_id": inserted_row[0],
        "created_on": inserted_row[1].strftime("%Y-%m-%d %H:%M:%S") if inserted_row[1] else None,
        "created_by": inserted_row[2],
        "email": user.email,
        "password": user.password,
        "is_active": user.is_active,
        "role_id": user.role_id,
        "company_id": user.company_id
    }


@router.get("/allusers", response_model=List[User])
def get_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
            SELECT
                u.UserId,
                u.Email,
                u.Password,
                u.IsActive,
                u.RoleId,
                u.CompanyId,
                u.CreatedOn,
                u.CreatedBy,
                u.UpdatedOn,
                u.UpdatedBy,
                u.DeletedOn,
                u.DeletedBy,

                c.Email AS CreatedByEmail,
                up.Email AS UpdatedByEmail,
                d.Email AS DeletedByEmail

            FROM TaskManager.dbo.Users u
            LEFT JOIN TaskManager.dbo.Users c ON u.CreatedBy = c.UserId
            LEFT JOIN TaskManager.dbo.Users up ON u.UpdatedBy = up.UserId
            LEFT JOIN TaskManager.dbo.Users d ON u.DeletedBy = d.UserId
            WHERE u.IsActive = 1
            """
            cursor.execute(query)
            rows = cursor.fetchall()

    return [
        User(
            user_id=row[0],
            email=row[1],
            password=row[2],
            is_active=bool(row[3]),
            role_id=row[4],
            company_id=row[5],
            created_on=row[6].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[6], datetime) else None,
            created_by=int(row[7]) if row[7] is not None else None,
            updated_on=row[8].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[8], datetime) else None,
            updated_by=int(row[9]) if row[9] is not None else None,
            deleted_on=row[10].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[10], datetime) else None,
            deleted_by=int(row[11]) if row[11] is not None else None,
        )
        for row in rows
    ]

@router.post("/users", response_model=User)
def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [1]:  # Example: only role ID 1 can create users
        raise HTTPException(status_code=403, detail="Not authorized.")

@router.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if user exists and is active (only active users can be updated)
                cursor.execute("SELECT UserId, IsActive FROM TaskManager.dbo.Users WHERE UserId = ?", (user_id,))
                existing_user = cursor.fetchone()
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")
                if existing_user.IsActive != 1:
                    raise HTTPException(status_code=400, detail=f"User with ID {user_id} is inactive and cannot be updated.")

                update_data = user.model_dump(exclude_unset=True)

                # Validate updated_by user if provided
                if "updated_by" in update_data:
                    cursor.execute("SELECT 1 FROM TaskManager.dbo.Users WHERE UserId = ? AND IsActive = 1", (update_data["updated_by"],))
                    if not cursor.fetchone():
                        raise HTTPException(status_code=400, detail=f"UpdatedBy user ID {update_data['updated_by']} not found or inactive.")

                # Validate role_id if provided (must be active)
                if "role_id" in update_data:
                    cursor.execute("SELECT 1 FROM TaskManager.dbo.Role WHERE RoleId = ? AND IsActive = 1", (update_data["role_id"],))
                    if not cursor.fetchone():
                        raise HTTPException(status_code=400, detail=f"Role with ID {update_data['role_id']} not found or inactive.")

                field_mapping = {
                    "email": "Email",
                    "password": "Password",
                    "is_active": "IsActive",
                    "updated_by": "UpdatedBy",
                    "role_id": "RoleId",
                    "company_id": "CompanyId"
                }

                fields = []
                values = []

                for field, value in update_data.items():
                    if field in field_mapping:
                        fields.append(f"{field_mapping[field]} = ?")
                        values.append(value)

                if not fields:
                    raise HTTPException(status_code=400, detail="No valid fields provided to update")

                fields.append("UpdatedOn = GETDATE()")

                query = f"UPDATE TaskManager.dbo.Users SET {', '.join(fields)} WHERE UserId = ?"
                values.append(user_id)

                cursor.execute(query, values)
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"User {user_id} updated successfully!"}
@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # ✅ Check if Employee exists
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Employee WHERE EmpId = ?", (emp_id,))
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=404, detail=f"Employee with ID {emp_id} not found.")

                # ✅ Soft delete from Employee table
                cursor.execute("""
                    UPDATE TaskManager.dbo.Employee 
                    SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? 
                    WHERE EmpId = ?
                """, (emp_id, emp_id))

                # ✅ Soft delete from Users table using same EmpId as DeletedBy
                cursor.execute("""
                    UPDATE TaskManager.dbo.Users 
                    SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? 
                    WHERE UserId = ?
                """, (emp_id, emp_id))

                conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"Employee and User with ID {emp_id} soft-deleted successfully."}



@router.post("/users/paginated", response_model=Dict[str, Any])
def get_paginated_users(pagination: UserPaginationRequest):
    try:
        page = pagination.page
        page_limit = pagination.PageLimit
        offset = (page - 1) * page_limit

        # Build WHERE clauses dynamically
        filters = ["IsActive = 1"]
        params = []

        if pagination.company_id:
            filters.append("CompanyId = ?")
            params.append(pagination.company_id)

        if pagination.role_id:
            filters.append("RoleId = ?")
            params.append(pagination.role_id)

        if pagination.search:
            filters.append("Email LIKE ?")
            params.append(f"%{pagination.search}%")

        where_clause = " AND ".join(filters)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Count total filtered users
                count_query = f"SELECT COUNT(*) FROM TaskManager.dbo.Users WHERE {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]

                if total_count == 0:
                    return {
                        "data": [],
                        "total": 0,
                        "page": page,
                        "PageLimit": page_limit,
                        "total_pages": 0
                    }

                # Fetch paginated filtered users
                data_query = f"""
                    SELECT
                        UserId,
                        Email,
                        Password,
                        IsActive,
                        RoleId,
                        CompanyId,
                        CreatedOn,
                        CreatedBy,
                        UpdatedOn,
                        UpdatedBy,
                        DeletedOn,
                        DeletedBy
                    FROM TaskManager.dbo.Users
                    WHERE {where_clause}
                    ORDER BY UserId
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """
                cursor.execute(data_query, params + [offset, page_limit])
                rows = cursor.fetchall()

        data = [
            User(
                user_id=row[0],
                email=row[1],
                password=row[2],
                is_active=bool(row[3]),
                role_id=row[4],
                company_id=row[5],
                created_on=row[6].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[6], datetime) else None,
                created_by=row[7],
                updated_on=row[8].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[8], datetime) else None,
                updated_by=row[9],
                deleted_on=row[10].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[10], datetime) else None,
                deleted_by=row[11]
            ).dict()
            for row in rows
        ]

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": page_limit,
            "total_pages": (total_count + page_limit - 1) // page_limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

