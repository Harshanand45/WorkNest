from typing import Any, Dict
from fastapi import APIRouter, HTTPException
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
                cursor.execute("SELECT CompanyId FROM TaskManager.dbo.Company WHERE CompanyId = ?", (role.company_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"Company ID {role.company_id} does not exist.")

                # ✅ Ensure CreatedBy (UserId) exists
                cursor.execute("SELECT UserId FROM TaskManager.dbo.Users WHERE UserId = ?", (role.created_by,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"CreatedBy user ID {role.created_by} does not exist.")

                cursor.execute("""
                    INSERT INTO TaskManager.dbo.Role (Role, CompanyId, IsActive, CreatedBy, CreatedOn)
                    OUTPUT INSERTED.RoleId, INSERTED.CreatedOn
                    VALUES (?, ?, ?, ?, GETDATE())
                """, (role.role, role.company_id, int(role.is_active), role.created_by))
                
                row = cursor.fetchone()
                conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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
@router.get("/allroles")
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
                    C.Name AS CompanyName  -- 🛠 Change 'Name' to actual company name column
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
                    "SELECT 1 FROM TaskManager.dbo.Users WHERE UserId = ? AND IsActive = 1",
                    (update_data['updated_by'],)
                )
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"UpdatedBy user ID {update_data['updated_by']} not found or inactive.")

                # Fetch existing role data
                cursor.execute("""
                    SELECT Role, CompanyId 
                    FROM TaskManager.dbo.Role 
                    WHERE RoleId = ?
                """, (role_id,))
                existing = cursor.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="Role not found.")

                existing_data = {
                    "role": existing[0],
                    "company_id": existing[1]
                }

                # Check that new values differ from existing ones
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
                        fields.append(f"{field_mapping[key]} = ?")
                        values.append(val)

                # Auto-set IsActive and UpdatedOn
                fields.append("IsActive = 1")
                fields.append("UpdatedOn = GETDATE()")

                query = f"""
                    UPDATE TaskManager.dbo.Role 
                    SET {', '.join(fields)} 
                    WHERE RoleId = ?
                """
                values.append(role_id)

                cursor.execute(query, values)
                conn.commit()

        return {"message": f"Role {role_id} updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Soft delete a role
@router.delete("/roles/{role_id}")
def delete_role(role_id: int, deleted_by: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if role exists
                cursor.execute("SELECT RoleId FROM TaskManager.dbo.Role WHERE RoleId = ?", (role_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail=f"Role ID {role_id} not found.")

                # Ensure deleted_by exists
                cursor.execute("SELECT UserId FROM TaskManager.dbo.Users WHERE UserId = ?", (deleted_by,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail=f"DeletedBy user ID {deleted_by} does not exist.")

                cursor.execute("""
                    UPDATE TaskManager.dbo.Role
                    SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ?
                    WHERE RoleId = ?
                """, (deleted_by, role_id))
                conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"Role {role_id} deleted by user {deleted_by}."}


@router.post("/roles/paginated", response_model=Dict[str, Any])
def get_paginated_roles(pagination: RolePaginationRequest):
    try:
        page = pagination.page
        page_limit = pagination.PageLimit  # or use pagination.page_limit if you renamed it
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
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """, (offset, page_limit))

                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                roles = [dict(zip(columns, row)) for row in rows]

        return {
            "data": roles,
            "total": total_count,
            "page": page,
            "PageLimit": page_limit,  # keep PascalCase if frontend expects it
            "total_pages": (total_count + page_limit - 1) // page_limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
