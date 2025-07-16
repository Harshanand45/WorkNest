import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { AdminRoutingModule } from './admin-routing.module';
import { AdashboardComponent } from './adashboard/adashboard.component';
import { AhomeComponent } from './Employees/employee/ahome/ahome.component';
import { ChartModule } from 'primeng/chart';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { EmployeeComponent } from './Employees/employee/employee.component';
import { AddComponent } from './Employees/employee/add/add.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { EditComponent } from './Employees/employee/edit/edit.component';
import { ProjectComponent } from './Projects/project/project.component';
import { AddprojectComponent } from './Projects/project/addproject/addproject.component';
import { EditprojectComponent } from './Projects/project/editproject/editproject.component';
import { ViewprojectComponent } from './Projects/project/viewproject/viewproject.component';
import { TaskComponent } from './Tasks/task/task.component';
import { AddtaskComponent } from './Tasks/task/addtask/addtask.component';
import { EdittaskComponent } from './Tasks/task/edittask/edittask.component';
import { ViewtaskComponent } from './Tasks/task/viewtask/viewtask.component';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { QuillModule } from 'ngx-quill';
import { ReportComponent } from './report/report.component';
import { HttpClientModule } from '@angular/common/http';
import { ProfileComponent } from './profile/profile.component';
import { EditprofileComponent } from './profile/editprofile/editprofile.component';


@NgModule({
  declarations: [
    AdashboardComponent,
    AhomeComponent,
    EmployeeComponent,
    AddComponent,
    EditComponent,
    ProjectComponent,
    AddprojectComponent,
    EditprojectComponent,
    ViewprojectComponent,
    TaskComponent,
    AddtaskComponent,
    EdittaskComponent,
    ViewtaskComponent,
    ReportComponent,
    ProfileComponent,
    EditprofileComponent,

  ],
  imports: [
    CommonModule,
    AdminRoutingModule,
    ChartModule,
    CardModule,
    TableModule,
    FormsModule,
    ReactiveFormsModule,
     MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    QuillModule,
    HttpClientModule

  ], 

  exports:[
    AdashboardComponent,
    AhomeComponent,
    EmployeeComponent,
    AddComponent,
    EditComponent,
    ProjectComponent,
    AddprojectComponent,
    EditprojectComponent,
    ViewprojectComponent,
    TaskComponent,
    AddtaskComponent,
    EdittaskComponent,
    ViewtaskComponent,
    ReportComponent,
    ProfileComponent,
    EditprofileComponent,

  ]
})
export class AdminModule { }
