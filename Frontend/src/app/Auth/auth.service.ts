import { Injectable } from '@angular/core';
import {jwtDecode} from 'jwt-decode';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor() {}

  isLoggedIn(): boolean {
    return !!localStorage.getItem('token');
  }

  getUser(): any {
    const userJson = localStorage.getItem('user');
    return userJson ? JSON.parse(userJson) : null;
  }

  getRole(): string | null {
    const user = this.getUser();
    return user?.role || null;
  }

  login(token: string): void {
    localStorage.setItem('token', token);

    // Decode and store user info
    const decoded: any = jwtDecode(token);
    localStorage.setItem('user', JSON.stringify({
      user_id: decoded.user_id,
      email: decoded.sub,
      role: decoded.role
    }));
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }
}
