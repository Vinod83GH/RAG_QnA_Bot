import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { ReactiveFormsModule } from '@angular/forms'; // Import this module
import { AppRoutingModule } from './app-routing.module';
import { FileUploadFormComponent } from './file-upload-form/file-upload-form.component';
import { AppComponent } from './app.component';
import { LoginComponent } from './login/login.component';
import { HttpClientModule } from '@angular/common/http'; // <-- Import HttpClientModule

@NgModule({
  declarations: [AppComponent, LoginComponent, FileUploadFormComponent],
  imports: [BrowserModule, AppRoutingModule, ReactiveFormsModule, HttpClientModule],
  providers: [],
  bootstrap: [AppComponent],
})
export class AppModule {}
