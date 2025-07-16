import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { AdashboardComponent } from '../Admin/adashboard/adashboard.component';
import { AhomeComponent } from '../Admin/Employees/employee/ahome/ahome.component';

import { AddComponent } from '../Admin/Employees/employee/add/add.component';
import { EditComponent } from '../Admin/Employees/employee/edit/edit.component';
import { ProjectComponent } from '../Admin/Projects/project/project.component';
import { AddprojectComponent } from '../Admin/Projects/project/addproject/addproject.component';
import { EditprojectComponent } from '../Admin/Projects/project/editproject/editproject.component';
import { ViewprojectComponent } from '../Admin/Projects/project/viewproject/viewproject.component';
import { TaskComponent } from '../Admin/Tasks/task/task.component';
import { EditprofileComponent } from '../Admin/profile/editprofile/editprofile.component';
import { ProfileComponent } from '../Admin/profile/profile.component';
import { ReportComponent } from '../Admin/report/report.component';
import { ViewtaskComponent } from '../Admin/Tasks/task/viewtask/viewtask.component';
import { EdittaskComponent } from '../Admin/Tasks/task/edittask/edittask.component';
import { AddtaskComponent } from '../Admin/Tasks/task/addtask/addtask.component';

import { EmployeeComponent } from '../Admin/Employees/employee/employee.component';
import { HomeComponent } from './home/home.component';
import { RolesComponent } from './roles/roles.component';

const routes: Routes = [
   {
    path: '',
    component: AdashboardComponent,
      children:[{
        path:'',
        component:AhomeComponent
      },{
         
      path: 'Employee',
      component: EmployeeComponent
    
      },
      {
       path:'roles',
       component:RolesComponent

      },
      {
        path: 'home',
        component: HomeComponent
      },
      {
        path: 'addemp',
        component: AddComponent
      },
      {
        path: 'editemp/:id',
        component: EditComponent
      },
      {
        path: 'project',
        component: ProjectComponent
      },
      {
        path: 'add',
        component: AddprojectComponent
      },
      {
        path:'editpro/:id',
        component:EditprojectComponent
      },
      {
        path:'viewproject/:id',
        component:ViewprojectComponent
      },
      {
        path:'task',
        component:TaskComponent
      },
      {
        path: 'addtask',
        component: AddtaskComponent
      },
      {
        path: 'edit-task/:id',
        component: EdittaskComponent
        
      },{
        path: 'viewtask/:id',
        component: ViewtaskComponent
      },{
        path:'report',
        component:ReportComponent
      },
      {
        path: 'Profile',
        component: ProfileComponent
      },
      {
        path:'Editprofile',
        component:EditprofileComponent
      }
        
    ]
    }
  
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class SuperAdminRoutingModule { }
