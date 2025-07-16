import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ProjectCreate {
  Name: string;
  StartDate: string;
  EndDate: string;
  ProjectManager: number;
  Priority: string;
  Status: string;
  CreatedBy: number;
  IsActive: boolean;
  CompanyId: number;
  Description: string;
}

export interface ProjectUpdate {
  Name?: string;
  StartDate?: string;
  EndDate?: string;
  ProjectManager?: number;
  Priority?: string;
  Status?: string;
  UpdatedBy: number;
  IsActive?: boolean;
  Description?: string;
}

export interface ProjectOut {
  ProjectId: number;
  Name: string;
  StartDate: string;
  EndDate: string;
  ProjectManager: number;
  Priority: string;
  Status: string;
  CreatedOn: string;
  CreatedBy: number;
  UpdatedOn?: string;
  UpdatedBy?: number;
  IsActive: boolean;
  DeletedOn?: string;
  DeletedBy?: number;
  CompanyId: number;
  Description: string;
}

export interface ProjectPaginationRequest {
  page: number;
  PageLimit: number;
  name?: string;
  status?: string;
  priority?: string;
  project_manager?: number; // 👈 Add this
}

@Injectable({
  providedIn: 'root'
})
export class ProjectService {
  private apiUrl = 'https://worknest-backend-3goy.onrender.com'; // ✅ Change this to your FastAPI base URL

  constructor(private http: HttpClient) {}

  createProject(project: ProjectCreate): Observable<any> {
    return this.http.post(`${this.apiUrl}/projects`, project);
  }

  updateProject(projectId: number, project: ProjectUpdate): Observable<any> {
    return this.http.put(`${this.apiUrl}/projects/${projectId}`, project);
  }

  deleteProject(projectId: number, deletedBy: number): Observable<any> {
    const params = new HttpParams().set('deleted_by', deletedBy);
    return this.http.delete(`${this.apiUrl}/projects/${projectId}`, { params });
  }

  getAllProjects(): Observable<ProjectOut[]> {
    return this.http.get<ProjectOut[]>(`${this.apiUrl}/allprojects`);
  }

  getPaginatedProjects(pagination: ProjectPaginationRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/projects/paginated`, pagination);
  }
  getProjectsByManager(empId: number): Observable<ProjectOut[]> {
  const params = new HttpParams().set('emp_id', empId.toString());
  return this.http.get<ProjectOut[]>(`${this.apiUrl}/projects/by-manager`, { params });
}
getProjectById(projectId: number): Observable<ProjectOut> {
  return this.http.get<ProjectOut>(`${this.apiUrl}/projects/${projectId}`);
}

}

