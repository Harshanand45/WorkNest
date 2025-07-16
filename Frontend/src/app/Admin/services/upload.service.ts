import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class UploadService {
  private uploadUrl = 'http://localhost:8000/upload'; // FastAPI upload endpoint

  constructor(private http: HttpClient) {}

  uploadDocument(file: File): Observable<{ filename: string; url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<{ filename: string; url: string }>(this.uploadUrl, formData);
  }
}
