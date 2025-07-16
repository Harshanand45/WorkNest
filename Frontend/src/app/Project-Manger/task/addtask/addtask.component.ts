import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { NgForm } from '@angular/forms';
import { ProjectService, ProjectOut } from '../../../Admin/services/projects.service';
import { ProjectEmployeeService, ProjectEmployee } from '../../../Admin/services/employee-project.service';
import { Task, TaskService } from '../../../Admin/services/tasks.service';
import { Employee, EmployeesService } from '../../../Admin/services/employees.service';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-addtask',
  standalone: false,
  templateUrl: './addtask.component.html',
  styleUrls: ['./addtask.component.css']
})
export class AddtaskComponent implements OnInit {
  selectedFiles: File[] = [];
  documentURLs: string[] = [];

  employees: Employee[] = [];
  assignedEmployees: Employee[] = [];
  projects: ProjectOut[] = [];
  allAssignments: ProjectEmployee[] = [];

  task: Partial<Task> = {
    Name: '',
    ProjectId: 0,
    AssignedTo: 0,
    Deadline: '',
    Priority: 'Low',
    Status: '',
    CompanyId: 1,
    CreatedBy: 0,
    Description: '',
    DocumentName: '',
    DocumentPath: '',
    DocumentUrl: ''
  };
    quillModules = {
    toolbar: [
      ['bold', 'italic', 'underline'],
      [{ header: 1 }, { header: 2 }],
      [{ list: 'ordered' }, { list: 'bullet' }],
      ['link', 'image'],
      ['clean']
    ]
  };
  selectedProjectId: number = 0;

  constructor(
    private taskService: TaskService,
    private employeeService: EmployeesService,
    private projectService: ProjectService,
    private projectEmployeeService: ProjectEmployeeService,
    private router: Router,
     private http: HttpClient 
  ) {}

  ngOnInit(): void {
    const createdBy = localStorage.getItem('empid');
    const companyId = localStorage.getItem('companyId');

    this.task.CreatedBy = createdBy ? +createdBy : 0;
    this.task.CompanyId = companyId ? +companyId : 0;

    this.loadEmployees(); 
    this.loadProjects();
  }

  loadEmployees(): void {
  this.employeeService.getAllEmployees().subscribe({
    next: (data) => {
      console.log("Employees fetched in Addtask:", data);
      this.employees = data;
    },
    error: (err) => console.error('Error loading employees:', err)
  });
}

  

  loadProjects(): void {
  const managerId = localStorage.getItem('empid');
  if (!managerId) {
    console.error('Manager ID not found in localStorage');
    return;
  }

  this.projectService.getProjectsByManager(+managerId).subscribe({
    next: (data) => (this.projects = data),
    error: (err) => console.error('Error loading manager projects:', err)
  });
}


  onProjectChange(projectId: number): void {
  this.selectedProjectId = +projectId;

  if (!this.selectedProjectId) {
    this.assignedEmployees = [];
    this.task.AssignedTo = 0;
    return;
  }
  const com=Number(localStorage.getItem("companyId"))
  console.log(com,this.selectedProjectId)
  this.projectEmployeeService.getByCompanyAndProject(com, this.selectedProjectId, 'active').subscribe({
    next: (data) => {
       console.log("Matched Employees from API:", data); // Debugging
         const assignedEmpIds = data.map(emp => emp.EmpId); // Extract all employee IDs
      console.log("Extracted Employee IDs:", assignedEmpIds);
      this.assignedEmployees = this.employees.filter(emp => assignedEmpIds.includes(emp.emp_id)); // Use 'id' instead of 'empId' if needed



      if (!this.assignedEmployees.some(e => e.emp_id === this.task.AssignedTo)) {
        this.task.AssignedTo = 0;
      }
    },
    error: (err) => console.error('Error fetching project-employee assignments:', err)
  });
}
  onFilesSelected(event: any): void {
  const file: File = event.target.files?.[0];

  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  this.http.post<{ filename: string, url: string }>('http://localhost:8000/upload', formData)
    .subscribe({
      next: (res) => {
        this.task.DocumentName = res.filename;
        this.task.DocumentPath = `uploads/${res.filename}`;
        this.task.DocumentUrl = `http://localhost:8000${res.url}`;
      },
      error: (err) => {
        console.error('File upload failed:', err);
        alert('File upload failed. Please try again.');
      }
    });
}

  getEmployeeName(empId: number): string {
    const employee = this.employees.find(e => e.emp_id === empId);
    return employee ? employee.name : 'Unknown';
  }

  onSubmit(form: NgForm): void {
    if (form.invalid) {
      Object.values(form.controls).forEach(control => control.markAsTouched());
      return;
    }

    this.taskService.createTask(this.task as Task).subscribe({
      next: () => {
        form.resetForm({ Priority: 'Low' });
        this.router.navigate(['/project-manger/task']);
      },
      error: (err) => console.error('Error creating task:', err)
    });
  }
}