import { ApplicationConfig } from '@angular/core';
import { provideRouter, Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { DashboardComponent } from './dashboard/dashboard.component';
import { FileUploadFormComponent } from './file-upload-form/file-upload-form.component';
import { provideHttpClient } from '@angular/common/http';

// Define your app routes
const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' }, // Redirect base path
  { path: 'login', component: LoginComponent },         // Route for login page
  { path: 'dash', component: DashboardComponent },         // Route for login page
  { path: 'upload-file', component: FileUploadFormComponent },   // Route for file upload
  { path: '**', redirectTo: 'login' },                  // Fallback for undefined paths
];

// Configure the application
export const appConfig: ApplicationConfig = {
  providers: [provideRouter(routes), provideHttpClient()],
};
