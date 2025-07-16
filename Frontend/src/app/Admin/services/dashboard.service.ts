import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';
export interface ProjectOut {
  ProjectId: number;
  Name: string;
  StartDate: string;
  EndDate: string;
  ProjectManager: number;
  Priority: 'High' | 'Medium' | 'Low';
  Status: 'Ongoing' | 'Completed' | 'Pending';
  CreatedOn: string;
  CreatedBy: number;
  UpdatedOn?: string;
  UpdatedBy?: number;
  IsActive: boolean;
  DeletedOn?: string;
  DeletedBy?: number;
  CompanyId: number;
  Description?: string;
}
export interface TaskOut {
  TaskId: number;
  Name: string;
  ProjectId: number;
  AssignedTo?: number | null;
  DocumentPath?: string | null;
  DocumentUrl?: string | null;
  Deadline?: string | null; // ISO string
  Priority?: string | null;
  Status?: string | null;
  CreatedOn: string; // ISO date string
  CreatedBy: number;
  UpdatedOn?: string | null;
  UpdatedBy?: number | null;
  DeletedOn?: string | null;
  DeletedBy?: number | null;
  CompanyId: number;
  Description?: string | null;
  DocumentName?: string | null;
  IsActive: boolean;
}


@Injectable({
  providedIn: 'root'
})
export class DashboardService {

 private baseUrl = 'http://localhost:8000'; // adjust your API base URL here

  constructor(private http: HttpClient) {}

    getAllProjects(): Observable<ProjectOut[]> {
    return this.http.get<ProjectOut[]>(`${this.baseUrl}/allprojects`);
  }


  getRecentTasks(): Observable<TaskOut[]> {
    const companyId = Number(localStorage.getItem('companyId'));
    const now = new Date();

    return this.http.get<TaskOut[]>(`${this.baseUrl}/alltasks`).pipe(
      map(tasks =>
        tasks.filter(task =>
          task.CompanyId === companyId &&
          task.CreatedOn &&
          (now.getTime() - new Date(task.CreatedOn).getTime()) <= 48 * 60 * 60 * 1000
        )
      )
    );
  }
}
