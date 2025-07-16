import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormArray } from '@angular/forms';
import { Router } from '@angular/router';
import { ProjectService } from '../../../services/projects.service';
import { EmployeesService, Employee } from '../../../services/employees.service';
import { ProjectRoleOut, ProjectRoleService } from '../../../services/project-role.service';
import { ProjectEmployeeService } from '../../../services/employee-project.service';

interface AssignedEmployee {
  empId: number;
  roleId: number;
}

@Component({
  selector: 'app-addproject',
  templateUrl: './addproject.component.html',
  styleUrl: './addproject.component.css',
  standalone:false
})
export class AddprojectComponent implements OnInit {
  projectForm: FormGroup;
  employees: Employee[] = [];
  roles: ProjectRoleOut[] = [];
  ui=Number(localStorage.getItem('roleid'))

  priorities = ['Low', 'Medium', 'High', 'Critical'];
  statuses = ['Not Started', 'Ongoing', 'Completed', 'On Hold', 'Pending'];

  constructor(
    private fb: FormBuilder,
    private projectService: ProjectService,
    private employeeService: EmployeesService,
    private roleService: ProjectRoleService,
    private projectEmployeeService: ProjectEmployeeService,
    private router: Router
  ) {
    this.projectForm = this.fb.group({
      projectTitle: ['', Validators.required],
      startDate: ['', Validators.required],
      endDate: ['', Validators.required],
      projectManager: ['', Validators.required],
      priority: ['', Validators.required],
      status: [[], Validators.required],
      description: [''],
      assignedEmployees: this.fb.array([])  // List of { empId, roleId }
    });
  }

  ngOnInit() {
    const companyId = Number(localStorage.getItem('companyId'));

    // Load employees
    this.employeeService.getAllEmployees().subscribe(allEmployees => {
      this.employees = allEmployees.filter(emp => emp.company_id === companyId && emp.role_id !== 8);
    });

    // Load project roles
    this.roleService.getProjectRoles().subscribe(data => {
      this.roles = data.filter(role => role.IsActive);
    });
  }

  get assignedEmployees(): FormArray {
    return this.projectForm.get('assignedEmployees') as FormArray;
  }

  addAssignedEmployee() {
    this.assignedEmployees.push(this.fb.group({
      empId: ['', Validators.required],
      roleId: ['', Validators.required]
    }));
  }

  removeAssignedEmployee(index: number) {
    this.assignedEmployees.removeAt(index);
  }

  onSubmit() {
    if (this.projectForm.invalid) {
      this.projectForm.markAllAsTouched();
      return;
    }

    const startDate = new Date(this.projectForm.value.startDate);
    const endDate = new Date(this.projectForm.value.endDate);

    if (endDate < startDate) {
      alert('End date cannot be earlier than start date.');
      return;
    }

    const newProject = {
      Name: this.projectForm.value.projectTitle,
      StartDate: this.projectForm.value.startDate,
      EndDate: this.projectForm.value.endDate,
      ProjectManager: Number(this.projectForm.value.projectManager),
      Priority: this.projectForm.value.priority,
      Status: this.projectForm.value.status.join(','),
      Description: this.projectForm.value.description,
      CreatedBy: Number(localStorage.getItem('empid')),
      CompanyId: Number(localStorage.getItem('companyId')),
      IsActive: true
    };

    // Create project
    this.projectService.createProject(newProject).subscribe({
      next: (res: any) => {
        const projectId = res?.project_id;


        // Prepare employee assignments
     const assignments = (this.projectForm.value.assignedEmployees as AssignedEmployee[]).map(a => ({
  EmpId: a.empId,
  ProjectId: projectId,
  CreatedBy: Number(localStorage.getItem('empid')),
  CompanyId: Number(localStorage.getItem('companyId')),
  ProjectRoleId: a.roleId
}));
 console.log('Assignment Payload:', assignments);
        // Save assignments
        assignments.forEach(assignment => {
          this.projectEmployeeService.create(assignment).subscribe();
        });

        alert('Project and assignments created successfully.');
        if(this.ui===8){
        this.router.navigate(['/admin/project']);
        }
        else{
          this.router.navigate(['/superadmin/project']);
        }
      },
      error: err => {
        alert('Failed to create project.');
        console.error(err);
      }
    });
  }
  back(){
     if(this.ui===8){
        this.router.navigate(['/admin/project']);
        }
        else{
          this.router.navigate(['/superadmin/project']);
        }

  }
}
