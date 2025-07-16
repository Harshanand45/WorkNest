import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { EmployeeRoutingModule } from './employee-routing.module';
import { EdashboardComponent } from './edashboard/edashboard.component';
import { HomeComponent } from './home/home.component';
import { ChartModule } from 'primeng/chart';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TaskComponent } from './Task/task/task.component';
import { TaskviewComponent } from './Task/taskview/taskview.component';



@NgModule({
  declarations: [
    EdashboardComponent,
    HomeComponent,
    TaskComponent,
    TaskviewComponent,
  ],
  imports: [
    CommonModule,
    EmployeeRoutingModule,
    ChartModule,
    CardModule,
    TableModule,
    FormsModule,
    ReactiveFormsModule,
     
  ]
})
export class EmployeeModule { }
