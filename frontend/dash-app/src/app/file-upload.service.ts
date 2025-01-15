import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',  // <-- Ensure provided in root or module
})
export class FileUploadService {
  private apiUrl = 'https://your-api-endpoint.com/upload'; // Replace with your actual API endpoint

  constructor(private http: HttpClient) {}

  uploadFile(
    file: File,
    collectionName: string,
    authToken: string
  ): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection_name', collectionName);

    const headers = new HttpHeaders().set('Authorization', `Bearer ${authToken}`);

    return this.http.post<any>(this.apiUrl, formData, { headers });
  }
}
