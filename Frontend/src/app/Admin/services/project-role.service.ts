import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ProjectRoleCreate {
  Role: string;
  CreatedBy: number;
  CompanyId: number;
}

export interface ProjectRoleUpdate {
  Role?: string;
  UpdatedBy: number;
  CompanyId?: number;
}

export interface ProjectRoleOut {
  ProjectRoleId: number;
  Role: string;
  CreatedOn: string;
  CreatedBy: number;
  UpdatedOn?: string | null;
  UpdatedBy?: number | null;
  IsActive: number | boolean;
  DeletedOn?: string | null;
  DeletedBy?: number | null;
  CompanyId?: number;
}

@Injectable({
  providedIn: 'root',
})
export class ProjectRoleService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  // List all active project roles
  getProjectRoles(): Observable<ProjectRoleOut[]> {
    return this.http.get<ProjectRoleOut[]>(`${this.baseUrl}/projectroles`);
  }

  // Create a new project role
  createProjectRole(data: ProjectRoleCreate): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.baseUrl}/project-roles`, data);
  }

  // Update existing project role by ID
  updateProjectRole(roleId: number, data: ProjectRoleUpdate): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(`${this.baseUrl}/project-roles/${roleId}`, data);
  }

  // Soft delete project role by ID with deleted_by as query param
  deleteProjectRole(roleId: number, deletedBy: number): Observable<{ message: string }> {
    const params = new HttpParams().set('deleted_by', deletedBy.toString());
    return this.http.delete<{ message: string }>(`${this.baseUrl}/project-roles/${roleId}`, { params });
  }
}
