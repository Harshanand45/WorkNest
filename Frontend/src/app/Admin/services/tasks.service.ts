import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Task {
  TaskId: number;
  Name: string;
  ProjectId: number;
  AssignedTo?: number;
  DocumentPath?: string;
  DocumentUrl?: string;
  Deadline: string;
  Priority: string;
  Status: string;
  CreatedOn?: string;
  CreatedBy: number;
  UpdatedOn?: string;
  UpdatedBy?: number;
  DeletedOn?: string;
  DeletedBy?: number;
  CompanyId: number;
  Description: string;
  DocumentName?: string;
  ExptedHours?: number; 
  IsActive?: boolean;
}

export interface PaginatedTaskRequest {
  page: number;
  PageLimit: number;
  ProjectName?: string;
  AssignedTo?: number;
  Priority?: string;
  TaskName?: string;
  ManagerId?:number
}

export interface PaginatedTaskResponse {
  data: Task[];
  total: number;
  page: number;
  PageLimit: number;
  total_pages: number;
}

@Injectable({
  providedIn: 'root'
})
export class TaskService {
  private baseUrl = 'https://worknest-backend-3goy.onrender.com';

  constructor(private http: HttpClient) {}

  createTask(task: Task): Observable<Task> {
    return this.http.post<Task>(`${this.baseUrl}/tasks`, task);
  }

  updateTask(taskId: number, task: Partial<Task>): Observable<Task> {
    return this.http.put<Task>(`${this.baseUrl}/tasks/${taskId}`, task);
  }

  deleteTask(taskId: number, deletedBy: number): Observable<{ message: string }> {
    const params = new HttpParams().set('deleted_by', deletedBy.toString());
    return this.http.delete<{ message: string }>(`${this.baseUrl}/tasks/${taskId}`, { params });
  }

  getAllTasks(): Observable<Task[]> {
    return this.http.get<Task[]>(`${this.baseUrl}/alltasks`);
  }

  getFilteredPaginatedTasks(filters: PaginatedTaskRequest): Observable<PaginatedTaskResponse> {
    return this.http.post<PaginatedTaskResponse>(`${this.baseUrl}/tasks/paginated/filter`, filters);
  }
  getTasksByManager(managerId: number): Observable<Task[]> {
  return this.http.get<Task[]>(`${this.baseUrl}/tasks/by-manager/${managerId}`);
}
getTasksByEmployee(empId: number): Observable<any[]> {
  return this.http.get<any[]>(`${this.baseUrl}/tasks/by-assigned/${empId}`);
}

}

