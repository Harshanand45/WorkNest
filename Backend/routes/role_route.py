from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
import pymssql # Changed from pyodbc
from db_connection import get_connection
from tables.role import Role, RoleCreate, RolePaginationRequest, RoleUpdate
from datetime import datetime

router = APIRouter()

# ✅ Create a role
@router.post("/roles", response_model=Role)
def create_role(role: RoleCreate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # ✅ Ensure CompanyId exists
                cursor.execute("SELECT CompanyId FROM TaskManager.dbo.Company WHERE CompanyId = %s", (role.company_id,)) # Changed ? to %s
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"Company ID {role.company_id} does not exist.")

                # ✅ Ensure CreatedBy (UserId) exists
                cursor.execute("SELECT UserId FROM TaskManager.dbo.Users WHERE UserId = %s", (role.created_by,)) # Changed ? to %s
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"CreatedBy user ID {role.created_by} does not exist.")

                cursor.execute("""
                    INSERT INTO TaskManager.dbo.Role (Role, CompanyId, IsActive, CreatedBy, CreatedOn)
                    OUTPUT INSERTED.RoleId, INSERTED.CreatedOn
                    VALUES (%s, %s, %s, %s, GETDATE())
                """, (role.role, role.company_id, int(role.is_active), role.created_by)) # Changed ? to %s and ensured tuple

                row = cursor.fetchone()
                conn.commit()

    except pymssql.Error as e: # Catch pymssql specific errors
        # Rollback is handled by the context manager if an exception occurs before commit,
        # but explicit rollback is good practice if not using context manager for connection.
        # For `with conn:`, `conn.rollback()` might be needed if `conn.commit()` fails or
        # if you have multiple operations within the `try` block that need atomic rollback.
        conn.rollback() # Explicit rollback on database error
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        conn.rollback() # Rollback for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Ensure row is not None before accessing elements
    if not row:
        raise HTTPException(status_code=500, detail="Failed to retrieve inserted role data.")

    return {
        "role_id": row[0],
        "role": role.role,
        "company_id": role.company_id,
        "is_active": role.is_active,
        "created_by": role.created_by,
        "created_on": row[1],
        "updated_on": None,
        "updated_by": None,
        "deleted_on": None,
        "deleted_by": None
    }

# ✅ Get all active roles with joins
@router.get("/allroles", response_model=List[Dict[str, Any]]) # Added response_model for clarity
def get_roles():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT
                    R.RoleId,
                    R.Role,
                    R.CreatedOn,
                    R.CreatedBy,
                    CU.Email AS CreatedByEmail,
                    R.UpdatedOn,
                    R.UpdatedBy,
                    UU.Email AS UpdatedByEmail,
                    R.IsActive,
                    R.DeletedOn,
                    R.DeletedBy,
                    DU.Email AS DeletedByEmail,
                    R.CompanyId,
                    C.Name AS CompanyName
                FROM TaskManager.dbo.Role R
                INNER JOIN TaskManager.dbo.Company C ON R.CompanyId = C.CompanyId
                LEFT JOIN TaskManager.dbo.Users CU ON R.CreatedBy = CU.UserId
                LEFT JOIN TaskManager.dbo.Users UU ON R.UpdatedBy = UU.UserId
                LEFT JOIN TaskManager.dbo.Users DU ON R.DeletedBy = DU.UserId
                WHERE R.IsActive = 1
                ORDER BY R.RoleId DESC
                """
                cursor.execute(query)
                rows = cursor.fetchall()

                columns = [column[0] for column in cursor.description]
                roles = [dict(zip(columns, row)) for row in rows]

        return roles

    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# ✅ Update a role
@router.put("/roles/{role_id}")
def update_role(role_id: int, role: RoleUpdate):
    try:
        update_data = role.model_dump(exclude_unset=True)

        # 'updated_by' must be provided
        if 'updated_by' not in update_data:
            raise HTTPException(status_code=400, detail="'updated_by' is required.")

        # At least one other field must be provided
        non_meta_fields = [key for key in update_data if key != 'updated_by']
        if not non_meta_fields:
            raise HTTPException(
                status_code=400,
                detail="At least one updatable field (e.g., role, company_id) must be provided."
            )

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if updated_by user exists and is active
                cursor.execute(
                    "SELECT 1 FROM TaskManager.dbo.Users WHERE UserId = %s AND IsActive = 1", # Changed ? to %s
                    (update_data['updated_by'],)
                )
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"UpdatedBy user ID {update_data['updated_by']} not found or inactive.")

                # Fetch existing role data
                cursor.execute("""
                    SELECT Role, CompanyId
                    FROM TaskManager.dbo.Role
                    WHERE RoleId = %s
                """, (role_id,)) # Changed ? to %s
                existing = cursor.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Role not found.")

                existing_data = {
                    "role": existing[0],
                    "company_id": existing[1]
                }

                # Check that new values differ from existing ones
                # Note: This comparison might need refinement for datetime/date objects
                no_change = all(
                    str(update_data.get(field)) == str(existing_data.get(field))
                    for field in non_meta_fields
                    if field in existing_data
                )

                if no_change:
                    raise HTTPException(status_code=400, detail="New values must be different from existing ones.")

                # Prepare update query
                field_mapping = {
                    "role": "Role",
                    "company_id": "CompanyId",
                    "updated_by": "UpdatedBy"
                }

                fields = []
                values = []

                for key, val in update_data.items():
                    if key in field_mapping:
                        fields.append(f"{field_mapping[key]} = %s") # Changed ? to %s
                        values.append(val)

                # Auto-set IsActive and UpdatedOn
                fields.append("IsActive = 1")
                fields.append("UpdatedOn = GETDATE()")

                query = f"""
                    UPDATE TaskManager.dbo.Role
                    SET {', '.join(fields)}
                    WHERE RoleId = %s
                """ # Changed ? to %s
                values.append(role_id)

                cursor.execute(query, tuple(values)) # Ensure values is a tuple
                conn.commit()

        return {"message": f"Role {role_id} updated successfully."}

    except pymssql.Error as e: # Catch pymssql specific errors
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# ✅ Soft delete a role
@router.delete("/roles/{role_id}")
def delete_role(role_id: int, deleted_by: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if role exists
                cursor.execute("SELECT RoleId FROM TaskManager.dbo.Role WHERE RoleId = %s", (role_id,)) # Changed ? to %s
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail=f"Role ID {role_id} not found.")

                # Ensure deleted_by exists
                cursor.execute("SELECT UserId FROM TaskManager.dbo.Users WHERE UserId = %s", (deleted_by,)) # Changed ? to %s
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"DeletedBy user ID {deleted_by} does not exist.")

                cursor.execute("""
                    UPDATE TaskManager.dbo.Role
                    SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s
                    WHERE RoleId = %s
                """, (deleted_by, role_id)) # Changed ? to %s and ensured tuple
                conn.commit()

    except pymssql.Error as e: # Catch pymssql specific errors
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    return {"message": f"Role {role_id} deleted by user {deleted_by}."}


@router.post("/roles/paginated", response_model=Dict[str, Any])
def get_paginated_roles(pagination: RolePaginationRequest):
    try:
        page = pagination.page
        page_limit = pagination.PageLimit
        offset = (page - 1) * page_limit

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Get total count of active roles
                cursor.execute("SELECT COUNT(*) FROM TaskManager.dbo.Role WHERE IsActive = 1")
                total_count = cursor.fetchone()[0]

                # Get paginated roles
                cursor.execute("""
                    SELECT
                        R.RoleId AS role_id,
                        R.Role AS role,
                        R.CompanyId AS company_id,
                        C.Name AS company_name,
                        R.CreatedOn AS created_on,
                        R.CreatedBy AS created_by,
                        CU.Email AS created_by_email,
                        R.UpdatedOn AS updated_on,
                        R.UpdatedBy AS updated_by,
                        UU.Email AS updated_by_email,
                        R.DeletedOn AS deleted_on,
                        R.DeletedBy AS deleted_by,
                        DU.Email AS deleted_by_email
                    FROM TaskManager.dbo.Role R
                    INNER JOIN TaskManager.dbo.Company C ON R.CompanyId = C.CompanyId
                    LEFT JOIN TaskManager.dbo.Users CU ON R.CreatedBy = CU.UserId
                    LEFT JOIN TaskManager.dbo.Users UU ON R.UpdatedBy = UU.UserId
                    LEFT JOIN TaskManager.dbo.Users DU ON R.DeletedBy = DU.UserId
                    WHERE R.IsActive = 1
                    ORDER BY R.RoleId DESC
                    OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """, (offset, page_limit)) # Changed ? to %s and ensured tuple

                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                roles = [dict(zip(columns, row)) for row in rows]

        return {
            "data": roles,
            "total": total_count,
            "page": page,
            "PageLimit": page_limit,
            "total_pages": (total_count + page_limit - 1) // page_limit
        }

    except pymssql.Error as e: # Catch pymssql specific errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")