import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { AuthGuard } from './auth.guard'; // adjust path as needed

const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  {
    path: 'admin',
    loadChildren: () => import('../Admin/admin.module').then(m => m.AdminModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'project-manager',
    loadChildren: () => import('../Project-Manger/projectmanager.module').then(m => m.ProjectmanagerModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'employee',
    loadChildren: () => import('../Employee/employee.module').then(m => m.EmployeeModule),
    canActivate: [AuthGuard]
  },
  {
    path: 'superadmin',
    loadChildren: () => import('../SuperAdmin/super-admin.module').then(m => m.SuperAdminModule),
    canActivate: [AuthGuard]
  }
];



@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AuthRoutingModule { }
