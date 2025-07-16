import os
import shutil
from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from routes.company_route import router as company_router
from routes.user_route import router as user_router
from routes.role_route import router as role_router
from routes.employee_route import router as employee_router
from routes.project_router import router as project_router
from routes.task_route import router as task_route
from routes.logtime_route import router as logtime_router
from routes.EmployeeProject_route import router as employeeProject_router
from routes.ProjectRole_router import router as ProjectRole_router
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_route import router as auth_router
app = FastAPI()

# Include company and user API routes
app.include_router(company_router, tags=["Company Management"])
app.include_router(user_router, tags=["User Management"])
app.include_router(role_router, tags=["Role Management"])
app.include_router(employee_router, tags=["Employee Management"])
app.include_router(project_router,tags=["Project Management"])
app.include_router(task_route,tags=["Task Management"])
app.include_router(logtime_router,tags=["Log Time Management"])
app.include_router(employeeProject_router,tags=["Employee Project Management"])
app.include_router(ProjectRole_router,tags=["Project Role Management"])
app.include_router(auth_router, tags=["Authentication"])


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static file serving
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# File upload endpoint
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "url": f"/uploads/{file.filename}"
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gorgeous-tartufo-872a99.netlify.app/login"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
