import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ProjectEmployee {
  projectEmployeeId?: number;
  EmpId: number;
  ProjectId: number;
  CreatedOn?: string;
  CreatedBy: number;
  IsActive?: boolean;
  DeletedOn?: string;
  DeletedBy?: number;
  CompanyId: number;
  ProjectRoleId: number;
  UpdatedOn?: string;
  UpdatedBy?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ProjectEmployeeService {
  private baseUrl = 'http://localhost:8000/project-employees';

  constructor(private http: HttpClient) {}

  // Fetch project employees by company and project
  getByCompanyAndProject(companyId: number, projectId: number, status: 'all' | 'active' | 'inactive' = 'active'): Observable<ProjectEmployee[]> {
    const params = new HttpParams()
      .set('company_id', companyId.toString())
      .set('project_id', projectId.toString())
      .set('status', status);
    
    return this.http.get<ProjectEmployee[]>(`${this.baseUrl}/by-company-project`, { params });
  }

  // Fetch all employees
  // ✅ CORRECT (POST request — if backend expects POST)
getAll(): Observable<ProjectEmployee[]> {
  const params = new HttpParams().set('status', 'active');
  return this.http.get<ProjectEmployee[]>(`${this.baseUrl}`, { params });
}


  // Create new project employee entry
  create(data: ProjectEmployee): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.baseUrl}`, data);
  }

  // Update an existing employee record
  update(id: number, data: Partial<ProjectEmployee>): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(`${this.baseUrl}/${id}`, data);
  }

  // Delete an employee record
  delete(id: number, deletedBy: number): Observable<{ message: string }> {
    const params = new HttpParams().set('deleted_by', deletedBy.toString());
    return this.http.delete<{ message: string }>(`${this.baseUrl}/${id}`, { params });
  }
}