import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ProjectmanagerRoutingModule } from './projectmanager-routing.module';
import { DashboardComponent } from './dashboard/dashboard.component';
import { HOMEComponent } from './home/home.component';
import { ChartModule } from 'primeng/chart';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { DropdownModule } from 'primeng/dropdown';
import { SelectModule } from 'primeng/select';
import { ProjectComponent } from './Project/project/project.component';
import { ViewprojectComponent } from './Project/project/viewproject/viewproject.component';
import { EditprojectComponent } from './Project/project/editproject/editproject.component';
import { TaskComponent } from './task/task/task.component';
import { EdittaskComponent } from './task/edittask/edittask.component';
import { AddtaskComponent } from './task/addtask/addtask.component';
import { ViewtaskComponent } from './task/viewtask/viewtask.component';
import { QuillModule } from 'ngx-quill';




@NgModule({
  declarations: [
  
  
    DashboardComponent,
           HOMEComponent,
           ProjectComponent,
           ViewprojectComponent,
           EditprojectComponent,
           TaskComponent,
           EdittaskComponent,
           AddtaskComponent,
           ViewtaskComponent,

  ],
  imports: [
    CommonModule,
    ProjectmanagerRoutingModule,
    ChartModule,
    CardModule,
    TableModule,
    FormsModule,
    ReactiveFormsModule,
    DropdownModule,
    SelectModule,
    QuillModule.forRoot()
  ]
})
export class ProjectmanagerModule { }
