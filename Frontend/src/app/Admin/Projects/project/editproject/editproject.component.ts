import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ProjectService, ProjectUpdate } from '../../../services/projects.service';
import { Employee, EmployeesService } from '../../../services/employees.service';
import { formatDate } from '@angular/common';

@Component({
  selector: 'app-editproject',
  standalone: false,
  templateUrl: './editproject.component.html',
  styleUrl: './editproject.component.css'
})
export class EditprojectComponent {
  projectForm!: FormGroup;
  employees: Employee[] = [];
    ui=Number(localStorage.getItem('roleid'))
  projectId!: number;
  priorities = ['Low', 'Medium', 'High', 'Critical'];
  statuses = ['Not Started', 'In Progress', 'Completed', 'On Hold', 'Pending'];

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private projectService: ProjectService,
    private employeeService: EmployeesService
  ) {}

 
  ngOnInit(): void {
    this.projectId = Number(this.route.snapshot.paramMap.get('id'));
    const companyId = Number(localStorage.getItem('companyId'));

    // Load employees and exclude role_id 8
    this.employeeService.getAllEmployees().subscribe((emps) => {
      this.employees = emps.filter(e => e.company_id === companyId && e.role_id !== 8);
    });

    // Load project by ID
    this.projectService.getAllProjects().subscribe((projects) => {
      const project = projects.find(p => p.ProjectId === this.projectId);
      if (!project) {
        alert('Project not found!');
        if(this.ui===8){
          this.router.navigate(['/admin/project']);
        }
        else{
          this.router.navigate(['/superadmin/project']);
        }
        
        return;
      }
      console.log('Loaded project:', project);

      // Format dates for date inputs
      const formattedStart = formatDate(project.StartDate, 'yyyy-MM-dd', 'en-US');
      const formattedEnd = formatDate(project.EndDate, 'yyyy-MM-dd', 'en-US');

      // Convert Status string to array for multi-select
      const statusArray = project.Status ? project.Status.split(',') : [];

      // Initialize form with status as array
      this.projectForm = this.fb.group({
        Name: [project.Name, Validators.required],
        StartDate: [formattedStart, Validators.required],
        EndDate: [formattedEnd, Validators.required],
        ProjectManager: [project.ProjectManager, Validators.required],
        Priority: [project.Priority, Validators.required],
        Status: [statusArray, Validators.required],
        Description: [project.Description || '', Validators.required],
      });
    });
  }

  onSubmit(): void {
    if (this.projectForm.invalid) {
      this.projectForm.markAllAsTouched();
      return;
    }

    const start = new Date(this.projectForm.value.StartDate);
    const end = new Date(this.projectForm.value.EndDate);
    if (end < start) {
      alert('End date cannot be before start date');
      return;
    }

    const updatedProject: ProjectUpdate = {
      Name: this.projectForm.value.Name,
      StartDate: this.projectForm.value.StartDate,
      EndDate: this.projectForm.value.EndDate,
      ProjectManager: Number(this.projectForm.value.ProjectManager),
      Priority: this.projectForm.value.Priority,
      Status: this.projectForm.value.Status.join(','),  // convert array to string
      UpdatedBy: Number(localStorage.getItem('empid')),
      IsActive: true,
      Description: this.projectForm.value.Description
    };

    this.projectService.updateProject(this.projectId, updatedProject).subscribe({
      next: () => {
        alert('Project updated successfully!');
         if(this.ui===8){
          this.router.navigate(['/admin/project']);
        }
        else{
          this.router.navigate(['/superadmin/project']);
        }
      },
      error: (err) => {
        console.error(err);
        alert('Failed to update project');
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
