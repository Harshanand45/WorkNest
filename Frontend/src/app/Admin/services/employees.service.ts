import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface Employee {
  emp_id: number;
  name: string;
  role_id: number;
  phone: string;
  address: string;
  email: string;
  description: string;
  created_by?: number;
  updated_by?: number;
  company_id: number;
  is_active?: boolean;
  created_on?: string;
  updated_on?: string;
  deleted_on?: string;
  deleted_by?: number;
  EmployeeImage:string;
    ImageUrl:string;
    ImagePath:string;
}
export interface RoleOption {
  role_id: number;
  role: string;
}

export interface EmployeePaginationRequest {
  page: number;
  page_limit: number;
}

export interface PaginatedEmployeeResponse {
  data: Employee[];
  total: number;
  page: number;
  page_limit: number;
  total_pages: number;
}
export interface EmployeePaginationRequest {
  page: number;
  page_limit: number;
  company_id?: number;
  role_id?: number;
  search?: string;
}

@Injectable({
  providedIn: 'root'
})
export class EmployeesService {
  addEmployee(employee: { name: string; role: string; phone: string; address: string; }) {
    throw new Error('Method not implemented.');
  }
  private baseUrl = 'https://worknest-backend-3goy.onrender.com'; // change this if hosted elsewhere

  constructor(private http: HttpClient) {}

  // ✅ Create employee
  createEmployee(emp: Partial<Employee>): Observable<any> {
    return this.http.post(`${this.baseUrl}/employees`, emp);
  }

  // ✅ Update employee
  updateEmployee(empId: number, emp: Partial<Employee>): Observable<any> {
    return this.http.put(`${this.baseUrl}/employees/${empId}`, emp);
  }

  // ✅ Soft delete employee
  deleteEmployee(empId: number, deletedBy: number): Observable<any> {
    const params = new HttpParams().set('deleted_by', deletedBy.toString());
    return this.http.delete(`${this.baseUrl}/employees/${empId}`, { params });
  }

  // ✅ Get all employees (active)
  getAllEmployees(): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.baseUrl}/allemployees`);
  }
    getRoleOptions(): Observable<RoleOption[]> {
    return this.http.get<RoleOption[]>(`${this.baseUrl}/allroles`);
  }

  // ✅ Get paginated employees
   getPaginatedEmployees(request: EmployeePaginationRequest): Observable<PaginatedEmployeeResponse> {
    return this.http.post<PaginatedEmployeeResponse>(`${this.baseUrl}/employees/paginated`, request);
  }

// ✅ Get tasks assigned to a specific employee



}
