import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AdashboardComponent } from './adashboard/adashboard.component';
import { AhomeComponent } from './Employees/employee/ahome/ahome.component';
import { EmployeeComponent } from './Employees/employee/employee.component';
import { AddComponent } from './Employees/employee/add/add.component';
import { EditComponent } from './Employees/employee/edit/edit.component';
import { ProjectComponent } from './Projects/project/project.component';
import { AddprojectComponent } from './Projects/project/addproject/addproject.component';
import { EditprojectComponent } from './Projects/project/editproject/editproject.component';
import { ViewprojectComponent } from './Projects/project/viewproject/viewproject.component';
import { TaskComponent } from './Tasks/task/task.component';
import { AddtaskComponent } from './Tasks/task/addtask/addtask.component';
import { EdittaskComponent } from './Tasks/task/edittask/edittask.component';
import { ViewtaskComponent } from './Tasks/task/viewtask/viewtask.component';
import { ReportComponent } from './report/report.component';
import { ProfileComponent } from './profile/profile.component';
import { EditprofileComponent } from './profile/editprofile/editprofile.component';

const routes: Routes = [
  {
    path: '',
    component: AdashboardComponent,
    children:[{
      path:'',
      component:AhomeComponent
    },{
       
    path: 'employee',
    component: EmployeeComponent
  
    },
    {
      path: 'home',
      component: AhomeComponent
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
      path: 'profile',
      component: ProfileComponent
    },
    {
      path:'editprofile',
      component:EditprofileComponent
    }
  ]
  }

];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AdminRoutingModule { }
