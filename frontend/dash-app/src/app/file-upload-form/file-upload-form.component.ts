import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms'; // <-- Import this
import { CommonModule } from '@angular/common';
import { FileUploadService } from '../file-upload.service'; // Import the service
import { HttpClientModule } from '@angular/common/http';  // <-- Import HttpClientModule in standalone component

@Component({
  selector: 'app-file-upload-form',
  templateUrl: './file-upload-form.component.html',
  standalone: true, // Indicates a standalone component
  imports: [CommonModule, HttpClientModule, ReactiveFormsModule], // Import ReactiveFormsModule here
  styleUrls: ['./file-upload-form.component.scss'],
})
export class FileUploadFormComponent {
  uploadForm: FormGroup;
  file: File | null = null;
  authToken: string = 'your-authentication-token-here'; // Replace with your actual token

  constructor(private fb: FormBuilder, private fileUploadService: FileUploadService) {
    this.uploadForm = this.fb.group({
      collectionName: ['', Validators.required],  // Text input field
      file: [null, Validators.required],           // File input field
    });
  }

  // Handle file input change
  onFileChange(event: any): void {
    const fileInput = event.target as HTMLInputElement;
    if (fileInput?.files?.length) {
      this.file = fileInput.files[0];
      this.uploadForm.patchValue({ file: this.file });
    }
  }

  // Handle form submission
  onSubmit(): void {
    if (this.uploadForm.valid && this.file) {
      const collectionName = this.uploadForm.get('collectionName')?.value;

      // Call the upload service to upload the file
      this.fileUploadService
        .uploadFile(this.file, collectionName, this.authToken)
        .subscribe(
          (response) => {
            console.log('File uploaded successfully!', response);
            alert('File uploaded successfully!');
          },
          (error) => {
            console.error('Error uploading file:', error);
            alert('Failed to upload file. Please try again.');
          }
        );
    } else {
      alert('Please fill in all fields and upload a file.');
    }
  }
}
