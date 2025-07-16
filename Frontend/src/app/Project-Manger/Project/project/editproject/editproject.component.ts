import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { EmployeesService, Employee } from '../../../../Admin/services/employees.service';
import { ProjectEmployeeService, ProjectEmployee } from '../../../../Admin/services/employee-project.service';
import { ProjectRoleService, ProjectRoleOut } from '../../../../Admin/services/project-role.service';

@Component({
  selector: 'app-editproject',
  standalone: false,
  templateUrl: './editproject.component.html',
  styleUrl: './editproject.component.css'
})
export class EditprojectComponent implements OnInit {
  employeeForm!: FormGroup;
  employees: Employee[] = [];
  roles: ProjectRoleOut[] = [];
  projectId!: number;
  companyId: number | null = null;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private employeeService: EmployeesService,
    private projectEmployeeService: ProjectEmployeeService,
    private roleService: ProjectRoleService
  ) {}

  ngOnInit(): void {
    this.projectId = Number(this.route.snapshot.paramMap.get('id'));

    // Fetch employees
    this.employeeService.getAllEmployees().subscribe(data => {
      this.employees = data;

      // Set companyId from any employee (assuming all employees belong to the same company)
      const currentEmpId = Number(localStorage.getItem('empid'));
      const currentUser = this.employees.find(e => e.emp_id === currentEmpId);
      this.companyId = currentUser?.company_id || null;
    });

    // Fetch roles
    this.roleService.getProjectRoles().subscribe(data => {
      this.roles = data;
    });

    // Build the form
    this.employeeForm = this.fb.group({
      EmpId: [null, Validators.required],
      ProjectRoleId: [null, Validators.required],
      CreatedOn: [new Date().toISOString().split('T')[0], Validators.required]
    });
  }

  onSubmit(): void {
    if (this.employeeForm.invalid) {
      this.employeeForm.markAllAsTouched();
      return;
    }

    const formData = this.employeeForm.value;
    const selectedEmployee = this.employees.find(
      e => e.emp_id === +formData.EmpId && e.company_id === this.companyId && e.role_id !== 8
    );

    if (!selectedEmployee) {
      alert('Selected employee not found or not eligible (maybe role is Admin)!');
      return;
    }

    const createdBy = Number(localStorage.getItem('empid'));

    const payload: ProjectEmployee = {
      EmpId: +formData.EmpId,
      ProjectId: this.projectId,
      CreatedBy: createdBy,
      CompanyId: selectedEmployee.company_id,
      ProjectRoleId: +formData.ProjectRoleId,
      CreatedOn: formData.CreatedOn
    };

    this.projectEmployeeService.create(payload).subscribe({
      next: () => {
        alert('Employee added to project successfully!');
        this.router.navigate(['/project-manager/project']);
      },
      error: (err) => {
        console.error('Error adding employee to project', err);
        alert('Failed to assign employee.');
      }
    });
  }
}
