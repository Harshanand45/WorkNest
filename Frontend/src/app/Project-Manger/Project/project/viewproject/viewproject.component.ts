import { Component } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ProjectService, ProjectOut } from '../../../../Admin/services/projects.service';
import { ProjectEmployeeService, ProjectEmployee } from '../../../../Admin/services/employee-project.service';
import { EmployeesService, Employee } from '../../../../Admin/services/employees.service';
import { ProjectRoleService, ProjectRoleOut } from '../../../../Admin/services/project-role.service';

@Component({
  selector: 'app-viewproject',
  standalone: false,
  templateUrl: './viewproject.component.html',
  styleUrl: './viewproject.component.css'
})
export class ViewprojectComponent {
  projectId!: number;
  project!: ProjectOut | null;
  assignedEmployees: ProjectEmployee[] = [];
  allEmployees: Employee[] = [];
  allRoles: ProjectRoleOut[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private projectService: ProjectService,
    private projectEmployeeService: ProjectEmployeeService,
    private employeeService: EmployeesService,
    private roleService: ProjectRoleService
  ) {}

  ngOnInit() {
    this.projectId = Number(this.route.snapshot.paramMap.get('id'));

    // Load all employees
    this.employeeService.getAllEmployees().subscribe(employees => {
      this.allEmployees = employees;

      // Load all roles
      this.roleService.getProjectRoles().subscribe(roles => {
        this.allRoles = roles;

        // Then load project
        this.projectService.getAllProjects().subscribe(projects => {
          this.project = projects.find(p => p.ProjectId === this.projectId) || null;

          if (!this.project) {
            alert('Project not found!');
            this.router.navigate(['/project-manager/project']);
            return;
          }

          // Load assigned employees
          this.loadAssignedEmployees(this.project.CompanyId, this.project.ProjectId);
        });
      });
    });
  }

  loadAssignedEmployees(companyId: number, projectId: number) {
    this.projectEmployeeService.getByCompanyAndProject(companyId, projectId).subscribe(
      (employees) => {
        this.assignedEmployees = employees;
      },
      (err) => {
        console.error('Failed to load assigned employees', err);
        this.assignedEmployees = [];
      }
    );
  }

  getEmployeeName(empId: number): string {
    const emp = this.allEmployees.find(e => e.emp_id === empId);
    return emp ? emp.name : 'Unknown';
  }

  getManagerName(): string {
    return this.project ? this.getEmployeeName(this.project.ProjectManager) : 'Unknown';
  }

  getRoleName(roleId: number): string {
    const role = this.allRoles.find(r => r.ProjectRoleId === roleId);
    return role ? role.Role : 'Unknown';
  }

  backToList() {
    this.router.navigate(['/project-manager/project']);
  }

  editProject(id: number) {
    this.router.navigate(['/project-manager/editpro', id]);
  }
}
