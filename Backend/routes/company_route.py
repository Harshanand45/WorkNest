from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from tables.company import Company, CompanyCreate, CompanyUpdate, CompanyPaginationRequest
from db_connection import get_connection
from datetime import datetime

router = APIRouter()

# ✅ Create a new company
@router.post("/companies", response_model=Company)

def create_company(comp: CompanyCreate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT 
                    c.CompanyId,
                    c.Name,
                    c.Email,
                    c.ContactNo,
                    c.Address,
                    c.IsActive,
                    c.CreatedOn,
                    c.UpdatedOn,
                    c.DeletedOn,

                    u1.UserId AS CreatedById,
                    u1.Email AS CreatedByEmail,

                    u2.UserId AS UpdatedById,
                    u2.Email AS UpdatedByEmail,

                    u3.UserId AS DeletedById,
                    u3.Email AS DeletedByEmail

                FROM TaskManager.dbo.Company c
                LEFT JOIN TaskManager.dbo.Users u1 ON c.CreatedBy = u1.UserId
                LEFT JOIN TaskManager.dbo.Users u2 ON c.UpdatedBy = u2.UserId
                LEFT JOIN TaskManager.dbo.Users u3 ON c.DeletedBy = u3.UserId
                """
                cursor.execute(query)
                cursor.execute("SELECT COUNT(*) FROM TaskManager.dbo.Company WHERE Name = ? OR Email = ?", (comp.name, comp.email))
                existing_company = cursor.fetchone()[0]
                if existing_company > 0:
                    raise HTTPException(status_code=400, detail="Company name or email already exists.")

                cursor.execute(
                    "INSERT INTO TaskManager.dbo.Company (Name, IsActive, CompanyDescription, CreatedBy, CompanyLogoName, CompanyLogoUrl, CompanyLogoPath, ContactNo, Email, Address) "
                    "OUTPUT INSERTED.CompanyId, INSERTED.CreatedOn, INSERTED.CreatedBy "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (comp.name, int(comp.is_active), comp.company_description, comp.created_by, comp.company_logo_name, 
                     comp.company_logo_url, comp.company_logo_path, comp.contact_no, comp.email, comp.address)
                )
                inserted_row = cursor.fetchone()
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "company_id": inserted_row[0],
        "created_on": inserted_row[1].strftime("%Y-%m-%d %H:%M:%S") if inserted_row[1] else None,
        "created_by": inserted_row[2],
        "name": comp.name,
        "company_logo_name": comp.company_logo_name,
        "company_logo_url": comp.company_logo_url,
        "company_logo_path": comp.company_logo_path,
        "company_description": comp.company_description,
        "contact_no": comp.contact_no,
        "email": comp.email,
        "address": comp.address,
        "is_active": comp.is_active
    }

# ✅ Get all companies
@router.get("/allcompanies", response_model=list[Company])
def get_companies():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM TaskManager.dbo.Company")
            rows = cursor.fetchall()

    return [
        Company(
            company_id=row[0],
            name=row[1],
            is_active=bool(row[2]),
            company_description=str(row[3]) if row[3] is not None else None,
            company_logo_name=row[10],
            company_logo_url=row[11],
            company_logo_path=row[12],
            contact_no=row[13],
            email=row[14],
            address=row[15],
            created_on=row[4].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[4], datetime) else None,
            created_by=int(row[5]) if row[5] is not None else 0,
            updated_on=row[6].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[6], datetime) else None,
            updated_by=int(row[7]) if isinstance(row[7], int) else None,
            deleted_on=row[8].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[8], datetime) else None,
            deleted_by=int(row[9]) if row[9] and str(row[9]).isdigit() else None
        )
        for row in rows
    ]

# ✅ Update company details
@router.put("/companies/{company_id}")
def update_company(company_id: int, comp: CompanyUpdate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if company exists and is active
                cursor.execute("""
                    SELECT CompanyId, IsActive 
                    FROM TaskManager.dbo.Company 
                    WHERE CompanyId = ?
                """, (company_id,))
                existing_row = cursor.fetchone()

                if not existing_row or existing_row.IsActive == 0:
                    raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found.")

                update_fields = [f"{field} = ?" for field in comp.dict(exclude_unset=True)]
                params = list(comp.dict(exclude_unset=True).values())

                update_fields.append("UpdatedBy = ?")
                params.append(comp.updated_by)
                update_fields.append("UpdatedOn = GETDATE()")

                update_query = f"UPDATE TaskManager.dbo.Company SET {', '.join(update_fields)} WHERE CompanyId = ?"
                params.append(company_id)

                cursor.execute(update_query, params)
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"Company {company_id} updated successfully!"}

# ✅ Soft delete a company
@router.delete("/companies/{company_id}")
def delete_company(company_id: int,deleted_by: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT CompanyId FROM TaskManager.dbo.Company WHERE CompanyId = ?", (company_id,))
                company_exists = cursor.fetchone()

                if not company_exists:
                    raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found.")

                cursor.execute(
                    "UPDATE TaskManager.dbo.Company SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = ? WHERE CompanyId = ?",
                    (deleted_by, company_id)
                )
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"Company {company_id} marked as deleted by user {deleted_by}."}



@router.post("/companies/paginated", response_model=Dict[str, Any])
def get_paginated_companies(pagination: CompanyPaginationRequest):
    try:
        page = pagination.page
        limit = pagination.limit
        offset = (page - 1) * limit

        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Total active company count
                cursor.execute("SELECT COUNT(*) FROM TaskManager.dbo.Company WHERE IsActive = 1")
                total_count = cursor.fetchone()[0]

                # Fetch paginated data
                cursor.execute("""
                    SELECT * FROM TaskManager.dbo.Company
                    WHERE IsActive = 1
                    ORDER BY CompanyId
                    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """, (offset, limit))

                rows = cursor.fetchall()

        data = [
            Company(
                company_id=row[0],
                name=row[1],
                is_active=bool(row[2]),
                company_description=str(row[3]) if row[3] is not None else None,
                company_logo_name=row[10],
                company_logo_url=row[11],
                company_logo_path=row[12],
                contact_no=row[13],
                email=row[14],
                address=row[15],
                created_on=row[4].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[4], datetime) else None,
                created_by=int(row[5]) if row[5] is not None else 0,
                updated_on=row[6].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[6], datetime) else None,
                updated_by=int(row[7]) if isinstance(row[7], int) else None,
                deleted_on=row[8].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row[8], datetime) else None,
                deleted_by=int(row[9]) if row[9] and str(row[9]).isdigit() else None
            ).dict()
            for row in rows
        ]

        return {
            "data": data,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
