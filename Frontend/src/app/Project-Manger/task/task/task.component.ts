import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Task, TaskService, PaginatedTaskRequest } from '../../../Admin/services/tasks.service';
import { ProjectOut, ProjectService } from '../../../Admin/services/projects.service';
import { Employee, EmployeesService } from '../../../Admin/services/employees.service';

@Component({
  selector: 'app-task',
  templateUrl: './task.component.html',
  styleUrls: ['./task.component.css'],
  standalone: false
})
export class TaskComponent implements OnInit {
  tasks: Task[] = [];
  projects: ProjectOut[] = [];
  employees: Employee[] = [];

  // Filters
  selectedProjectName: string = '';
  selectedEmployeeId: number | null = null;
  selectedPriority: string = '';
  searchTaskName: string = '';

  // Pagination
  currentPage: number = 1;
  pageLimit: number = 10;
  totalPages: number = 0;
  totalTasks: number = 0;

  managerId: number = 0;

  constructor(
    private taskService: TaskService,
    private projectService: ProjectService,
    private employeeService: EmployeesService,
    private router: Router
  ) {}

 ngOnInit(): void {
  const id = Number(localStorage.getItem('empid'));
  if (isNaN(id)) {
    console.error('Invalid empid in localStorage');
    return;
  }
  this.managerId = id;
  this.loadProjectsAndEmployees();
  this.searchTasks();
}


  loadProjectsAndEmployees(): void {
    this.projectService.getProjectsByManager(this.managerId).subscribe({
      next: (data) => (this.projects = data),
      error: (err) => console.error('Error fetching projects', err)
    });

    this.employeeService.getAllEmployees().subscribe({
      next: (data) => (this.employees = data),
      error: (err) => console.error('Error fetching employees', err)
    });
  }

  searchTasks(): void {
    const filters: PaginatedTaskRequest = {
      page: this.currentPage,
      PageLimit: this.pageLimit,
      ProjectName: this.selectedProjectName || undefined,
      AssignedTo: this.selectedEmployeeId || undefined,
      Priority: this.selectedPriority || undefined,
      TaskName: this.searchTaskName || undefined,
      ManagerId: this.managerId
    };

    this.taskService.getFilteredPaginatedTasks(filters).subscribe({
      next: (res) => {
        this.tasks = res.data;
        this.totalTasks = res.total;
        this.totalPages = res.total_pages;
      },
      error: (err) => console.error('Error fetching tasks', err)
    });
  }

  clearFilters(): void {
    this.selectedProjectName = '';
    this.selectedEmployeeId = null;
    this.selectedPriority = '';
    this.searchTaskName = '';
    this.currentPage = 1;
    this.searchTasks();
  }

  getProjectName(projectId: number | undefined): string {
    return this.projects.find(p => p.ProjectId === projectId)?.Name || 'Unknown';
  }

  getEmployeeName(empId: number | undefined): string {
    return this.employees.find(e => e.emp_id === empId)?.name || 'Unassigned';
  }

  onEdit(id: number): void {
    this.router.navigate(['/project-manager/edittask', id]);
  }

  onView(id: number): void {
    this.router.navigate(['/project-manager/viewtask', id]);
  }

  onDelete(id: number): void {
    const deletedByStr = localStorage.getItem('empid');
    if (!deletedByStr) return;
    const deletedBy = Number(deletedByStr);
    if (isNaN(deletedBy)) return;

    if (confirm('Are you sure you want to delete this task?')) {
      this.taskService.deleteTask(id, deletedBy).subscribe({
        next: () => this.searchTasks(),
        error: (err) => console.error('Delete failed', err)
      });
    }
  }

  onAdd(): void {
    this.router.navigate(['/project-manager/addtask']);
  }

  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    this.searchTasks();
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.searchTasks();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.searchTasks();
    }
  }
}
