import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ProjectOut, ProjectService } from '../../../services/projects.service';
import { ProjectEmployeeService } from '../../../services/employee-project.service';
import { EmployeesService, Employee } from '../../../services/employees.service';
import { ProjectRoleService, ProjectRoleOut } from '../../../services/project-role.service';

@Component({
  selector: 'app-viewproject',
  templateUrl: './viewproject.component.html',
  styleUrls: ['./viewproject.component.css'],
  standalone: false
})
export class ViewprojectComponent implements OnInit {
    ui=Number(localStorage.getItem('roleid'))
  project!: ProjectOut | undefined;
  assignedEmployees: {
    name: string;
    joinDate: string;
    endDate: string;
    role: string;
  }[] = [];
  projectId!: number;
  employees: Employee[] = [];
  roles: ProjectRoleOut[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private projectService: ProjectService,
    private projectEmployeeService: ProjectEmployeeService,
    private employeeService: EmployeesService,
    private projectRoleService: ProjectRoleService
  ) {}

  ngOnInit() {
    this.projectId = Number(this.route.snapshot.paramMap.get('id'));
    console.log('Component initialized. Project ID:', this.projectId);

    if (!this.projectId || isNaN(this.projectId)) {
      alert('Invalid Project ID');
       if(this.ui===8){
          this.router.navigate(['/admin/project']);
        }
        else{
          this.router.navigate(['/superadmin/project']);
        }
      return;
    }

    this.loadProjectDetails(this.projectId);
  }

loadProjectDetails(projectId: number) {
  forkJoin({
    employees: this.employeeService.getAllEmployees(),
    projects: this.projectService.getAllProjects(),
    assignments: this.projectEmployeeService.getAll(),
    roles: this.projectRoleService.getProjectRoles()
  }).subscribe({
    next: ({ employees, projects, assignments, roles }) => {
      this.employees = employees ?? [];
      this.roles = (roles ?? []).filter(r => r.IsActive === 1 || r.IsActive === true);

      // Find current project
      this.project = projects.find(p => Number(p.ProjectId) === projectId);
      if (!this.project) {
        alert('Project not found!');
        this.router.navigate(['/admin/project']);
        return;
      }

      // Filter assignments for this project
      const filteredAssignments = (assignments ?? []).filter((a: any) => {
        const pid = Number(a.ProjectId ?? a.projectId);
        return pid === projectId;
      });

      // Map assignments to employee detail
      this.assignedEmployees = filteredAssignments.map((a: any) => {
        const empId = Number(a.EmpId ?? a.emp_id ?? a.empId);
        const emp = this.employees.find(e => Number(e.emp_id) === empId);

        const roleId = Number(a.ProjectRoleId ?? a.projectRoleId ?? a.project_role_id);
        const joinDateRaw = a.CreatedOn ?? a.createdOn;
        const endDateRaw = a.DeletedOn ?? a.deletedOn;

        const joinDateFormatted = joinDateRaw ? new Date(joinDateRaw).toLocaleDateString() : 'N/A';
        const endDateFormatted = endDateRaw ? new Date(endDateRaw).toLocaleDateString() : 'Active';

        return {
          name: emp?.name ?? `Unknown (ID: ${empId})`,
          joinDate: joinDateFormatted,
          endDate: endDateFormatted,
          role: this.getRoleName(roleId)
        };
      });

      console.log('Assigned Employees:', this.assignedEmployees);
    },
   
  });
}


  getRoleName(roleId: number): string {
    if (!roleId) return 'Unknown Role';
    const role = this.roles.find(r => Number(r.ProjectRoleId) === roleId);
    return role?.Role ?? 'Unknown Role';
  }

  getProjectManagerName(empId: number): string {
    const emp = this.employees.find(e => Number(e.emp_id) === empId);
    return emp ? emp.name : 'Unknown Manager';
  }

  backToList() {
   if(this.ui===8){
          this.router.navigate(['/admin/project']);
        }
        else{
          this.router.navigate(['/superadmin/project']);
        }
  }
}
