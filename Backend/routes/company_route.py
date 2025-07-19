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
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute("SELECT COUNT(*) AS count FROM Company WHERE Name = %s OR Email = %s", (comp.name, comp.email))
                existing_company = cursor.fetchone()['count']
                if existing_company > 0:
                    raise HTTPException(status_code=400, detail="Company name or email already exists.")

                cursor.execute(
                    """
                    INSERT INTO Company (Name, IsActive, CompanyDescription, CreatedBy, CompanyLogoName, CompanyLogoUrl, CompanyLogoPath, ContactNo, Email, Address, CreatedOn)
                    OUTPUT INSERTED.CompanyId, INSERTED.CreatedOn, INSERTED.CreatedBy
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, GETDATE())
                    """,
                    (comp.name, int(comp.is_active), comp.company_description, comp.created_by, comp.company_logo_name, 
                     comp.company_logo_url, comp.company_logo_path, comp.contact_no, comp.email, comp.address)
                )
                inserted_row = cursor.fetchone()
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "company_id": inserted_row['CompanyId'],
        "created_on": inserted_row['CreatedOn'].strftime("%Y-%m-%d %H:%M:%S") if inserted_row['CreatedOn'] else None,
        "created_by": inserted_row['CreatedBy'],
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
        with conn.cursor(as_dict=True) as cursor:
            cursor.execute("SELECT * FROM Company")
            rows = cursor.fetchall()

    return [
        Company(
            company_id=row['CompanyId'],
            name=row['Name'],
            is_active=bool(row['IsActive']),
            company_description=row.get('CompanyDescription'),
            company_logo_name=row.get('CompanyLogoName'),
            company_logo_url=row.get('CompanyLogoUrl'),
            company_logo_path=row.get('CompanyLogoPath'),
            contact_no=row.get('ContactNo'),
            email=row.get('Email'),
            address=row.get('Address'),
            created_on=row['CreatedOn'].strftime("%Y-%m-%d %H:%M:%S") if row.get('CreatedOn') else None,
            created_by=row.get('CreatedBy', 0),
            updated_on=row['UpdatedOn'].strftime("%Y-%m-%d %H:%M:%S") if row.get('UpdatedOn') else None,
            updated_by=row.get('UpdatedBy'),
            deleted_on=row['DeletedOn'].strftime("%Y-%m-%d %H:%M:%S") if row.get('DeletedOn') else None,
            deleted_by=row.get('DeletedBy')
        )
        for row in rows
    ]

# ✅ Update company details
@router.put("/companies/{company_id}")
def update_company(company_id: int, comp: CompanyUpdate):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT CompanyId, IsActive FROM Company WHERE CompanyId = %s", (company_id,))
                existing_row = cursor.fetchone()

                if not existing_row or existing_row[1] == 0:
                    raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found.")

                update_fields = [f"{field} = %s" for field in comp.dict(exclude_unset=True)]
                params = list(comp.dict(exclude_unset=True).values())
                update_fields.append("UpdatedBy = %s")
                params.append(comp.updated_by)
                update_fields.append("UpdatedOn = GETDATE()")
                update_query = f"UPDATE Company SET {', '.join(update_fields)} WHERE CompanyId = %s"
                params.append(company_id)

                cursor.execute(update_query, tuple(params))
                conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": f"Company {company_id} updated successfully!"}

# ✅ Soft delete a company
@router.delete("/companies/{company_id}")
def delete_company(company_id: int, deleted_by: int):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT CompanyId FROM Company WHERE CompanyId = %s", (company_id,))
                company_exists = cursor.fetchone()

                if not company_exists:
                    raise HTTPException(status_code=404, detail=f"Company with ID {company_id} not found.")

                cursor.execute(
                    "UPDATE Company SET IsActive = 0, DeletedOn = GETDATE(), DeletedBy = %s WHERE CompanyId = %s",
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
            with conn.cursor(as_dict=True) as cursor:
                cursor.execute("SELECT COUNT(*) AS count FROM Company WHERE IsActive = 1")
                total_count = cursor.fetchone()['count']

                cursor.execute("""
                    SELECT * FROM Company
                    WHERE IsActive = 1
                    ORDER BY CompanyId
                    OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """, (offset, limit))
                rows = cursor.fetchall()

        data = [
            Company(
                company_id=row['CompanyId'],
                name=row['Name'],
                is_active=bool(row['IsActive']),
                company_description=row.get('CompanyDescription'),
                company_logo_name=row.get('CompanyLogoName'),
                company_logo_url=row.get('CompanyLogoUrl'),
                company_logo_path=row.get('CompanyLogoPath'),
                contact_no=row.get('ContactNo'),
                email=row.get('Email'),
                address=row.get('Address'),
                created_on=row['CreatedOn'].strftime("%Y-%m-%d %H:%M:%S") if row.get('CreatedOn') else None,
                created_by=row.get('CreatedBy', 0),
                updated_on=row['UpdatedOn'].strftime("%Y-%m-%d %H:%M:%S") if row.get('UpdatedOn') else None,
                updated_by=row.get('UpdatedBy'),
                deleted_on=row['DeletedOn'].strftime("%Y-%m-%d %H:%M:%S") if row.get('DeletedOn') else None,
                deleted_by=row.get('DeletedBy')
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