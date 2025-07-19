from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
import pymssql # Changed from pyodbc
from tables.users import User, UserCreate, UserUpdate, UserPaginationRequest
from db_connection import get_connection
from datetime import datetime
from tables.auth import get_current_user # Assuming this handles authentication and provides user role

router = APIRouter()

# Helper to validate if a user_id exists in Employee table
def check_user_exists(user_id: int, cursor: pymssql.Cursor) -> bool: # Changed type hint
    cursor.execute("SELECT EmpId FROM TaskManager.dbo.Employee WHERE EmpId = %s", (user_id,)) # Changed ? to %s
    return cursor.fetchone() is not None

# ✅ Create a new user with user existence validation and authorization
# Merged logic from both original create_user functions
@router.post("/users", response_model=User)
def create_user(user: UserCreate, db: pymssql.Connection = Depends(get_connection), # Changed type hint
                current_user: Dict[str, Any] = Depends(get_current_user)): # Added auth dependency
    # Authorization check
    # if current_user["role_id"] != 1: # Assuming 'role_id' is in current_user payload
    #     raise HTTPException(status_code=403, detail="Not authorized to create users.")
    # Based on the original code, `current_user["role"]` was used. Adjust as per actual auth payload.
    # Assuming role 1 is 'Admin' based on prior examples.
    if current_user["role"] not in [1]:
        raise HTTPException(status_code=403, detail="Not authorized to create users. Only administrators can perform this action.")

    try:
        with db.cursor() as cursor:
            # Check if email exists
            cursor.execute("SELECT COUNT(*) FROM TaskManager.dbo.Users WHERE Email = %s", (user.email,)) # Changed ? to %s
            if cursor.fetchone()[0] > 0:
                raise HTTPException(status_code=400, detail="Email already exists.")

            # Check if created_by user exists (in Employee table)
            if not check_user_exists(user.created_by, cursor):
                raise HTTPException(status_code=400, detail=f"CreatedBy user ID {user.created_by} not found in Employee records.")

            # Check if RoleId exists and is active
            cursor.execute("SELECT 1 FROM TaskManager.dbo.Role WHERE RoleId = %s AND IsActive = 1", (user.role_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Role ID {user.role_id} not found or inactive.")

            # Check if CompanyId exists
            cursor.execute("SELECT 1 FROM TaskManager.dbo.Company WHERE CompanyId = %s", (user.company_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Company ID {user.company_id} not found.")


            cursor.execute(
                "INSERT INTO TaskManager.dbo.Users "
                "(Email, Password, IsActive, CreatedBy, RoleId, CompanyId) "
                "OUTPUT INSERTED.UserId, INSERTED.CreatedOn, INSERTED.CreatedBy " # These are the columns returned by OUTPUT
                "VALUES (%s, %s, %s, %s, %s, %s)", # Changed ? to %s
                (user.email, user.password, int(user.is_active), user.created_by, user.role_id, user.company_id)
            )
            inserted_row_data = cursor.fetchone()
            db.commit()

        if not inserted_row_data:
            raise HTTPException(status_code=500, detail="Failed to retrieve inserted user data.")

    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback() # Rollback changes on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Map the output to the User model
    # inserted_row_data is a tuple: (UserId, CreatedOn, CreatedBy)
    return User(
        user_id=inserted_row_data[0],
        email=user.email, # From input model
        password=user.password, # From input model
        is_active=user.is_active, # From input model
        role_id=user.role_id, # From input model
        company_id=user.company_id, # From input model
        created_on=inserted_row_data[1].strftime("%Y-%m-%d %H:%M:%S") if isinstance(inserted_row_data[1], datetime) else None,
        created_by=inserted_row_data[2],
        updated_on=None, # Not set on creation
        updated_by=None, # Not set on creation
        deleted_on=None, # Not set on creation
        deleted_by=None # Not set on creation
    )

@router.get("/allusers", response_model=List[User])
def get_users(db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        with db.cursor() as cursor:
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
                -- Joining on Users table itself for CreatedBy, UpdatedBy, DeletedBy emails
                c.Email AS CreatedByEmail,
                up.Email AS UpdatedByEmail,
                d.Email AS DeletedByEmail
            FROM TaskManager.dbo.Users u
            LEFT JOIN TaskManager.dbo.Users c ON u.CreatedBy = c.UserId
            LEFT JOIN TaskManager.dbo.Users up ON u.UpdatedBy = up.UserId
            LEFT JOIN TaskManager.dbo.Users d ON u.DeletedBy = d.UserId
            WHERE u.IsActive = 1
            ORDER BY u.UserId DESC; -- Added ORDER BY for consistent results
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description] # Get column names

        return [
            User(
                user_id=row[columns.index('UserId')],
                email=row[columns.index('Email')],
                password=row[columns.index('Password')],
                is_active=bool(row[columns.index('IsActive')]),
                role_id=row[columns.index('RoleId')],
                company_id=row[columns.index('CompanyId')],
                created_on=row[columns.index('CreatedOn')].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[columns.index('CreatedOn')], datetime) else None,
                created_by=row[columns.index('CreatedBy')],
                updated_on=row[columns.index('UpdatedOn')].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[columns.index('UpdatedOn')], datetime) else None,
                updated_by=row[columns.index('UpdatedBy')],
                deleted_on=row[columns.index('DeletedOn')].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[columns.index('DeletedOn')], datetime) else None,
                deleted_by=row[columns.index('DeletedBy')]
            )
            for row in rows
        ]
    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        with db.cursor() as cursor:
            # Check if user exists and is active (only active users can be updated)
            cursor.execute("SELECT UserId, IsActive FROM TaskManager.dbo.Users WHERE UserId = %s", (user_id,)) # Changed ? to %s
            existing_user_data = cursor.fetchone()
            if not existing_user_data:
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found.")
            # Access IsActive by index, assuming it's the second column in the SELECT (index 1)
            if existing_user_data[1] != 1: # Assuming 1 means active
                raise HTTPException(status_code=400, detail=f"User with ID {user_id} is inactive and cannot be updated.")

            update_data = user.model_dump(exclude_unset=True)

            # Validate updated_by user if provided
            if "updated_by" in update_data:
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Users WHERE UserId = %s AND IsActive = 1", (update_data["updated_by"],)) # Changed ? to %s
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"UpdatedBy user ID {update_data['updated_by']} not found or inactive.")

            # Validate role_id if provided (must be active)
            if "role_id" in update_data:
                cursor.execute("SELECT 1 FROM TaskManager.dbo.Role WHERE RoleId = %s AND IsActive = 1", (update_data["role_id"],)) # Changed ? to %s
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"Role with ID {update_data['role_id']} not found or inactive.")

            field_mapping = {
                "email": "Email",
                "password": "Password",
                "is_active": "IsActive", # Will be 0 or 1, int(bool) handles this
                "updated_by": "UpdatedBy",
                "role_id": "RoleId",
                "company_id": "CompanyId"
            }

            fields_to_update = []
            values_to_update = []

            for field, value in update_data.items():
                if field in field_mapping:
                    # Convert boolean is_active to int for SQL
                    if field == "is_active":
                        value = int(value)
                    fields_to_update.append(f"{field_mapping[field]} = %s") # Changed ? to %s
                    values_to_update.append(value)

            if not fields_to_update:
                raise HTTPException(status_code=400, detail="No valid fields provided to update")

            fields_to_update.append("UpdatedOn = GETDATE()")

            query = f"UPDATE TaskManager.dbo.Users SET {', '.join(fields_to_update)} WHERE UserId = %s" # Changed ? to %s
            values_to_update.append(user_id) # Add user_id for the WHERE clause

            cursor.execute(query, tuple(values_to_update)) # Ensure values are passed as a tuple
            db.commit()
    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    return {"message": f"User {user_id} updated successfully!"}

@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        with db.cursor() as cursor:
            # ✅ Check if Employee exists
            cursor.execute("SELECT 1 FROM TaskManager.dbo.Employee WHERE EmpId = %s", (emp_id,)) # Changed ? to %s
            if cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail=f"Employee with ID {emp_id} not found.")

            # ✅ Soft delete from Employee table
            # Note: The original query used emp_id for DeletedBy. This implies the employee is deleting themselves
            # or it's a placeholder. If 'DeletedBy' should be an admin user, pass that ID instead of emp_id.
            # Assuming current logic (emp_id as DeletedBy) for conversion.
            cursor.execute("""
                UPDATE TaskManager.dbo.Employee
                SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s
                WHERE EmpId = %s
            """, (emp_id, emp_id)) # Changed ? to %s

            # ✅ Soft delete from Users table using same EmpId as DeletedBy (assuming UserId = EmpId for this scenario)
            cursor.execute("""
                UPDATE TaskManager.dbo.Users
                SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s
                WHERE UserId = %s
            """, (emp_id, emp_id)) # Changed ? to %s

            db.commit()

    except pymssql.Error as e: # Catch pymssql specific errors
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    return {"message": f"Employee and User with ID {emp_id} soft-deleted successfully."}


@router.post("/users/paginated", response_model=Dict[str, Any])
def get_paginated_users(pagination: UserPaginationRequest, db: pymssql.Connection = Depends(get_connection)): # Changed type hint
    try:
        page = pagination.page
        page_limit = pagination.PageLimit
        offset = (page - 1) * page_limit

        # Build WHERE clauses dynamically
        filters = ["IsActive = 1"]
        params = []

        if pagination.company_id:
            filters.append("CompanyId = %s") # Changed ? to %s
            params.append(pagination.company_id)

        if pagination.role_id:
            filters.append("RoleId = %s") # Changed ? to %s
            params.append(pagination.role_id)

        if pagination.search:
            filters.append("Email LIKE %s") # Changed ? to %s
            params.append(f"%{pagination.search}%")

        where_clause = " AND ".join(filters)

        with db.cursor() as cursor:
            # Count total filtered users
            count_query = f"SELECT COUNT(*) FROM TaskManager.dbo.Users WHERE {where_clause}"
            cursor.execute(count_query, tuple(params)) # Ensure params is a tuple
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
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """ # Changed ? to %s
            cursor.execute(data_query, tuple(params + [offset, page_limit])) # Ensure all params are in one tuple
            rows = cursor.fetchall()

        # Get column names from cursor description for robust mapping
        columns = [col[0] for col in cursor.description]

        data = [
            User(
                # Use dict(zip(columns, row)) for cleaner mapping to Pydantic model
                **dict(zip(columns, row))
            ).dict() # Convert to dict if User is a Pydantic model
            for row in rows
        ]

        # Post-process datetime objects for JSON serialization if needed
        for item in data:
            if isinstance(item.get("CreatedOn"), datetime):
                item["CreatedOn"] = item["CreatedOn"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(item.get("UpdatedOn"), datetime):
                item["UpdatedOn"] = item["UpdatedOn"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(item.get("DeletedOn"), datetime):
                item["DeletedOn"] = item["DeletedOn"].strftime("%Y-%m-%d %H:%M:%S")
            item["IsActive"] = bool(item["IsActive"]) # Ensure IsActive is boolean

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "PageLimit": page_limit,
            "total_pages": (total_count + page_limit - 1) // page_limit
        }

    except pymssql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")