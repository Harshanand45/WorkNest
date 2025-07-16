import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { SuperAdminRoutingModule } from './super-admin-routing.module';
import { DashboardComponent } from './dashboard/dashboard.component';
import { HomeComponent } from './home/home.component';
import { EmployeeComponent } from './employee/employee.component';
import { ProfileComponent } from './profile/profile.component';
import { ProjectsComponent } from './projects/projects.component';

import { ReportComponent } from './report/report.component';
import { TasksComponent } from './tasks/tasks.component';
import { RolesComponent } from './roles/roles.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ChartModule } from 'primeng/chart';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { QuillModule } from 'ngx-quill';
import { HttpClientModule } from '@angular/common/http';
import { AdminRoutingModule } from '../Admin/admin-routing.module';
import { AdminModule } from "../Admin/admin.module";


@NgModule({
  declarations: [
    DashboardComponent,
    HomeComponent,
    EmployeeComponent,
    ProfileComponent,
    ProjectsComponent,

    ReportComponent,
    TasksComponent,
    RolesComponent
  ],
  imports: [
    CommonModule,
    SuperAdminRoutingModule,
    ChartModule,
    CardModule,
    TableModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    QuillModule,
    HttpClientModule,
    AdminRoutingModule,
    AdminModule
]
})
export class SuperAdminModule { }
