from fastapi import APIRouter, HTTPException
from db_connection import get_connection
from jwt_handler import create_access_token

router = APIRouter()

@router.post("/login")
def login_user(credentials: dict):
    email = credentials.get("email")
    password = credentials.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UserId, RoleId, IsActive FROM TaskManager.dbo.Users WHERE Email = ? AND Password = ?",
            (email, password)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials.")
        if user[2] != 1:
            raise HTTPException(status_code=403, detail="User is inactive.")

        token = create_access_token({
            "sub": email,
            "user_id": user[0],
            "role": user[1]
        })
        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")
    finally:
        if conn:
            conn.close()
