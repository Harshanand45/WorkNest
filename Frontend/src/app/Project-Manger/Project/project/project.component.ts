import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ProjectService, ProjectOut } from '../../../Admin/services/projects.service';
import { Employee, EmployeesService } from '../../../Admin/services/employees.service';


@Component({
  selector: 'app-project',
  standalone: false,
  templateUrl: './project.component.html',
  styleUrl: './project.component.css'
})
export class ProjectComponent {
  projects: ProjectOut[] = [];
    employees: Employee[] = [];

  constructor(private projectService: ProjectService, private router: Router,private employeesService: EmployeesService) { }

  ngOnInit() {
    const empId = localStorage.getItem('empid');
    if (empId) {
      this.projectService.getProjectsByManager(+empId).subscribe({
        next: (res: ProjectOut[]) => {
          this.projects = res;
        },
        error: (err) => {
          console.error('Failed to load projects for manager:', err);
        }
      });
    } else {
      console.error('empid not found in localStorage');
    }
     this.employeesService.getAllEmployees().subscribe({
        next: (res: Employee[]) => {
          this.employees = res;
        },
        error: (err) => {
          console.error('Failed to load employees:', err);
        }
      });
  
  }

   getManagerName(managerId: number): string {
    const manager = this.employees.find(emp => emp.emp_id === managerId);
    return manager ? manager.name : 'Unknown';
  }
  editProject(id: number) {
    this.router.navigate(['/project-manager/editpro', id]);
  }

  viewProject(id: number) {
    this.router.navigate(['/project-manager/viewproject', id]);
  }

  deleteProject(id: number,empId :number) {
    this.projectService.deleteProject(id,empId).subscribe({
      next: () => {
        // Refresh the list
        this.ngOnInit();
      },
      error: (err) => {
        console.error('Failed to delete project:', err);
      }
    });
  }

  addProject() {
    this.router.navigate(['/admin/add']);
  }
}
