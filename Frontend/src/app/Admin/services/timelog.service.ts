import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Timelog {
  LogId?: number;
  empId: number;
  taskId: number;
  date: string;
  companyId: number;
  description: string;
  minutesSpent: number;
  hoursSpent: number;
  createdBy: number;
  createdOn?: string;
  isActive?: boolean;
}

@Injectable({ providedIn: 'root' })
export class TimeLogService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  addLog(log: Timelog): Observable<Timelog> {
    // Convert camelCase to PascalCase to match FastAPI
    const formattedLog = {
      EmpId: log.empId,
      TaskId: log.taskId,
      Date: log.date,
      CompanyId: log.companyId,
      Description: log.description,
      MinutesSpent: log.minutesSpent,
      HoursSpent: log.hoursSpent,
      CreatedBy: log.createdBy
    };

    return this.http.post<Timelog>(`${this.baseUrl}/logtimes`, formattedLog);
  }

  getLogsByTask(taskId: number): Observable<Timelog[]> {
    return this.http.get<Timelog[]>(`${this.baseUrl}/logtimes/by-task/${taskId}`);
  }

  getAllLogs(): Observable<Timelog[]> {
    return this.http.get<Timelog[]>(`${this.baseUrl}/alllogtimes`);
  }
}
