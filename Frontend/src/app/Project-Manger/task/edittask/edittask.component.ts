import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { Task, TaskService } from '../../../Admin/services/tasks.service';
import { Employee, EmployeesService } from '../../../Admin/services/employees.service';
import { ProjectOut, ProjectService } from '../../../Admin/services/projects.service';
import { formatDate } from '@angular/common';


@Component({
  selector: 'app-edittask',
  standalone: false,
  templateUrl: './edittask.component.html',
  styleUrls: ['./edittask.component.css']
})
export class EdittaskComponent implements OnInit {
    quillModules = {
    toolbar: [
      ['bold', 'italic', 'underline'],
      [{ header: 1 }, { header: 2 }],
      [{ list: 'ordered' }, { list: 'bullet' }],
      ['link', 'image'],
      ['clean']
    ]
  };
  taskForm!: FormGroup;
  taskId!: number;
  task?: Task;
  loading: boolean = true;

  employees: Employee[] = [];
  projects: ProjectOut[] = [];

  constructor(
    private fb: FormBuilder,
    private taskService: TaskService,
    private employeeService: EmployeesService,
    private projectService: ProjectService,
    private route: ActivatedRoute,
    private router: Router,
    private http: HttpClient  
  ) {}

  ngOnInit(): void {
    this.taskId = Number(this.route.snapshot.paramMap.get('id'));
    if (isNaN(this.taskId)) {
      alert('Invalid task ID');
      this.router.navigate(['/tasks']);
      return;
    }

    // Load Employees and Projects
    this.loadEmployees();
    this.loadProjects();
   

    // Load the task and initialize the form
    this.taskService.getAllTasks().subscribe({
      next: (tasks) => {
        this.task = tasks.find(t => t.TaskId === this.taskId);
        if (!this.task) {
          alert('Task not found!');
          this.router.navigate(['/tasks']);
          return;
        }

        this.initForm();
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load task:', err);
        alert('Failed to fetch task');
        this.router.navigate(['/tasks']);
      }
    });
  }
 
  initForm(): void {
 this.taskForm = this.fb.group({
  Name: [this.task?.Name || '', Validators.required],
  Priority: [this.task?.Priority || '', Validators.required],
  AssignedTo: [this.task?.AssignedTo || '', Validators.required],
  ProjectId: [this.task?.ProjectId || '', Validators.required],
  Deadline: [this.formatDateForInput(this.task?.Deadline), Validators.required],
  Description: [this.task?.Description || ''],
  DocumentName: [this.task?.DocumentName || ''],
  DocumentPath: [this.task?.DocumentPath || ''],
  DocumentUrl: [this.task?.DocumentUrl || '']
});

  }
  onFileChange(event: any): void {
  const file: File = event.target.files[0];
  if (file) {
    const formData = new FormData();
    formData.append('file', file);

    this.http.post<{ filename: string, url: string }>('http://localhost:8000/upload', formData)
      .subscribe({
        next: (res) => {
          this.taskForm.patchValue({
            DocumentName: res.filename,
            DocumentPath: `uploads/${res.filename}`,
            DocumentUrl: `http://localhost:8000${res.url}`
          });
        },
        error: (err) => {
          console.error("Upload failed", err);
        }
      });
  }
}


  
  loadEmployees(): void {
    this.employeeService.getAllEmployees().subscribe({
      next: (data) => (this.employees = data),
      error: (err) => console.error('Error loading employees', err)
    });
  }


formatDateForInput(dateString: string | undefined): string {
  if (!dateString) return '';
  try {
    return formatDate(dateString, 'yyyy-MM-dd', 'en-US');
  } catch {
    return '';
  }
}


 loadProjects(): void {
  const managerId = localStorage.getItem('empid');
  if (!managerId) {
    console.error("Manager ID not found in localStorage");
    return;
  }

  this.projectService.getProjectsByManager(+managerId).subscribe({
    next: (data) => {
      this.projects = data;
    },
    error: (err) => console.error('Error loading manager projects:', err)
  });
}


  onSubmit(): void {
    if (this.taskForm.invalid) {
      this.taskForm.markAllAsTouched();
      return;
    }

    const updatedBy = localStorage.getItem('empid');

    const updatedTask: Task = {
      TaskId: this.taskId,
      ...this.taskForm.value,
      UpdatedBy: updatedBy ? +updatedBy : undefined
    };

    this.taskService.updateTask(this.taskId, updatedTask).subscribe({
      next: () => {
        alert('Task updated successfully!');
        this.router.navigate(['']);
      },
      error: (err) => {
        console.error('Update failed:', err);
        alert('Task update failed!');
      }
    });
  }
}

