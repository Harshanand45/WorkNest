import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { jwtDecode } from 'jwt-decode';


export interface Role {
  RoleId: number;
  Role: string;
}
export interface Company {
  company_id: number;
  name: string;
}

export interface UserRegistration {
  user_id: number;
  email: string;
  password: string;
  role_id: number;
  created_by: number;
  is_active: boolean;
  company_id: number;
}

@Injectable({
  providedIn: 'root'
})
export class UserRoleService {
  private baseUrl = 'https://worknest-backend-3goy.onrender.com';

  constructor(private http: HttpClient) {}

  // 🔐 JWT login API call
  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/login`, { email, password });
  }

  // ✅ Store login info


storeToken(token: string): void {
  localStorage.setItem('token', token);
  const decoded: any = jwtDecode(token);
  console.log('Decoded Token:', decoded); // Check if company_id exists

  const user = {
    user_id: decoded.user_id,
    role_id: decoded.role,            // if role_id stored as "role" in token
    email: decoded.sub || decoded.email,
    company_id: decoded.company_id || 1  // Fallback if not in token
  };

  localStorage.setItem('user', JSON.stringify(user));
}



  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }

  getUser(): any {
    const userJson = localStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
  }

  getRole(): string | null {
    return this.getUser()?.role || null;
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // 🚀 Existing APIs below

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(`${this.baseUrl}/allroles`);
  }

  getAllUsers(): Observable<UserRegistration[]> {
    return this.http.get<UserRegistration[]>(`${this.baseUrl}/allusers`);
  }

  registerUser(user: UserRegistration): Observable<any> {
    return this.http.post(`${this.baseUrl}/users`, user);
  }

  deleteUser(userId: number, deletedBy: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/employees/${userId}?deleted_by=${deletedBy}`);
  }

  getAllCompanies(): Observable<Company[]> {
    return this.http.get<Company[]>(`${this.baseUrl}/allcompanies`);
  }
}
