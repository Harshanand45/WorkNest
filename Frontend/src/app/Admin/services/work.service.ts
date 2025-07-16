import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
export interface Employee {
  emp_id: number;
  name: string;
  role_id: number;
  phone: string;
  address: string;
  email: string;
  description: string;
  company_id: number;
  created_by: number;
  employee_img?: string;
  img_path?: string;
  img_url?: string;
  updated_by: number;
  is_active: boolean;
  created_on?: string;
  updated_on?: string;
  deleted_on?: string;
  deleted_by?: number;
}


@Injectable({
  providedIn: 'root'
})
export class WorkService {

   private baseUrl = 'http://localhost:8000'; // replace with your actual backend URL

  constructor(private http: HttpClient) {}

 getAllEmployees(): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.baseUrl}/allemployees`);
  }
  // ✅ Update employee with image (multipart/form-data)
updateEmployeeWithImage(empId: number, formData: FormData): Observable<any> {
  return this.http.put(`${this.baseUrl}/employees/${empId}`, formData);
}
}
