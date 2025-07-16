import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Role {
  role_id: number;
  role: string;
  company_id: number;
  is_active: boolean;
  created_by: number;
  created_on: string;
  updated_on?: string;
  updated_by?: number;
  deleted_on?: string;
  deleted_by?: number;
}

export interface RoleCreate {
  role: string;
  company_id: number;
  is_active: boolean;
  created_by: number;
}

export interface RoleUpdate {
  role?: string;
  company_id?: number;
  updated_by: number;
}

export interface RolePaginationRequest {
  page: number;
  PageLimit: number;
}

@Injectable({
  providedIn: 'root'
})
export class RolesService {
  private baseUrl = 'https://worknest-backend-3goy.onrender.com'; // Update to your actual FastAPI URL

  constructor(private http: HttpClient) {}

  // ✅ Create Role
  createRole(role: RoleCreate): Observable<Role> {
    return this.http.post<Role>(`${this.baseUrl}/roles`, role);
  }

  // ✅ Get All Active Roles (with joins)
  getAllRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(`${this.baseUrl}/allroles`);
  }

  // ✅ Update Role
  updateRole(roleId: number, role: RoleUpdate): Observable<{ message: string }> {
    return this.http.put<{ message: string }>(`${this.baseUrl}/roles/${roleId}`, role);
  }

  // ✅ Soft Delete Role
  deleteRole(roleId: number, deletedBy: number): Observable<{ message: string }> {
    const params = new HttpParams().set('deleted_by', deletedBy.toString());
    return this.http.delete<{ message: string }>(`${this.baseUrl}/roles/${roleId}`, { params });
  }

  // ✅ Get Paginated Roles
  getPaginatedRoles(pagination: RolePaginationRequest): Observable<{
    data: Role[];
    total: number;
    page: number;
    PageLimit: number;
    total_pages: number;
  }> {
    return this.http.post<{
      data: Role[];
      total: number;
      page: number;
      PageLimit: number;
      total_pages: number;
    }>(`${this.baseUrl}/roles/paginated`, pagination);
  }
}
