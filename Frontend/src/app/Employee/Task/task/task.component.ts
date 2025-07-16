import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Task, TaskService, PaginatedTaskRequest } from '../../../Admin/services/tasks.service';
import { EmployeesService, Employee } from '../../../Admin/services/employees.service';
import { ProjectService, ProjectOut } from '../../../Admin/services/projects.service';

@Component({
  selector: 'app-task',
  templateUrl: './task.component.html',
  styleUrls: ['./task.component.css'],
  standalone: false
})
export class TaskComponent implements OnInit {
  tasks: Task[] = [];
  employees: Employee[] = [];
  projects: ProjectOut[] = [];
  searchTaskName: string = '';

  // Filters
  selectedProjectName: string = '';
  selectedPriority: string = '';
  sortByDeadline: boolean = false;

  // Pagination
  currentPage: number = 1;
  pageLimit: number = 5;
  totalPages: number = 0;
  totalTasks: number = 0;

  empId: number = 0;

  constructor(
    private taskService: TaskService,
    private projectService: ProjectService,
    private employeeService: EmployeesService,
    private router: Router
  ) {}

  ngOnInit(): void {
    const empIdStr = localStorage.getItem('empid');
    if (!empIdStr) return;
    this.empId = Number(empIdStr);

    this.loadProjectsAndEmployees();
    this.searchTasks();
  }

  loadProjectsAndEmployees(): void {
    this.projectService.getAllProjects().subscribe({
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
      AssignedTo: this.empId, // 👈 Fetch tasks only for this employee
      Priority: this.selectedPriority || undefined,
      TaskName: this.searchTaskName || undefined
    };

    this.taskService.getFilteredPaginatedTasks(filters).subscribe({
      next: (res) => {
        this.tasks = res.data;
        this.totalTasks = res.total;
        this.totalPages = res.total_pages;
      },
      error: (err) => console.error('Error fetching filtered tasks', err)
    });
  }

  clearFilters(): void {
    this.selectedProjectName = '';
    this.selectedPriority = '';
    this.searchTaskName = '';
    this.currentPage = 1;
    this.searchTasks();
  }

  getEmployeeName(empId: number | undefined): string {
    return this.employees.find(e => e.emp_id === empId)?.name || 'Unknown';
  }

  getProjectName(projectId: number | undefined): string {
    return this.projects.find(p => p.ProjectId === projectId)?.Name || 'Unknown';
  }

  onView(id: number): void {
    this.router.navigate(['/employee/task', id]);
  }

  onAdd(): void {
    this.router.navigate(['/employee/todaywork']);
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

  searchEmployeesByName(name: string): Employee[] {
    const lowerName = name.toLowerCase();
    return this.employees.filter(emp => emp.name.toLowerCase().includes(lowerName));
  }
}
