import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard.component';
import { HOMEComponent } from './home/home.component';
import { ProjectComponent } from './Project/project/project.component';
import { ViewprojectComponent } from './Project/project/viewproject/viewproject.component';
import { EditprojectComponent } from './Project/project/editproject/editproject.component';
import { TaskComponent } from './task/task/task.component';
import { AddtaskComponent } from './task/addtask/addtask.component';
import { EdittaskComponent } from './task/edittask/edittask.component';
import { ViewtaskComponent } from './task/viewtask/viewtask.component';
import { ProfileComponent } from '../Admin/profile/profile.component';


const routes: Routes = [
  { 
    path:'',
    component:DashboardComponent,
    children:[{
      path:'',
      component:HOMEComponent
    },
    {
      path:'home',
      component:HOMEComponent
    },
    {
      path:'project',
      component:ProjectComponent
    },
    {
      path:'viewproject/:id',
      component:ViewprojectComponent
    },
    {
      path:'editpro/:id',
      component:EditprojectComponent
    },{
      path:'task',
      component:TaskComponent
    },
    {
      path:'addtask',
      component:AddtaskComponent
    }
    ,{
      path:'edittask/:id',
      component:EdittaskComponent
    },
    {
      path:'viewtask/:id',
      component:ViewtaskComponent
    }
  ]
 
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProjectmanagerRoutingModule { }
