import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { EdashboardComponent } from './edashboard/edashboard.component';
import { HomeComponent } from './home/home.component';
import { TaskComponent } from './Task/task/task.component';
import { TaskviewComponent } from './Task/taskview/taskview.component';

const routes: Routes = [
  {
    path: '',
    component: EdashboardComponent,
    children:[{
      path: '',
      component: HomeComponent
    },
    {
      path: 'home',
      component: HomeComponent
    },
    {
      path:'task',
      component:TaskComponent
    },{
      path: 'task/:id',
      component: TaskviewComponent
    },
   
    
  ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class EmployeeRoutingModule {

 }
