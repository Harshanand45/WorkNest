import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Task, TaskService, PaginatedTaskRequest } from '../../services/tasks.service';
import { EmployeesService, Employee } from '../../services/employees.service';
import { ProjectService, ProjectOut } from '../../services/projects.service';

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
  searchName: string = ''
  searchTaskName: string = '';
  ui=Number(localStorage.getItem('roleid'))

  // Filters
  selectedProjectName: string = '';
  selectedEmployeeId: number | null = null;
  selectedPriority: string = '';
  sortByDeadline: boolean = false;

  // Pagination
  currentPage: number = 1;
  pageLimit: number = 5;
  totalPages: number = 0;
  totalTasks: number = 0;

  constructor(
    private taskService: TaskService,
    private projectService: ProjectService,
    private employeeService: EmployeesService,
    private router: Router
  ) {}

  ngOnInit(): void {
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
    AssignedTo: this.selectedEmployeeId || undefined,
    Priority: this.selectedPriority || undefined,
    TaskName: this.searchTaskName || undefined   // ✅ Include this
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
    this.selectedEmployeeId = null;
    this.selectedPriority = '';
    this.sortByDeadline = false;
    this.currentPage = 1;
    this.searchTasks();
    this.searchTaskName = '';
  }

  getEmployeeName(empId: number | undefined): string {
    return this.employees.find(e => e.emp_id === empId)?.name || 'Unknown';
  }

  getProjectName(projectId: number | undefined): string {
    return this.projects.find(p => p.ProjectId === projectId)?.Name || 'Unknown';
  }

  onEdit(id: number): void {
    if(this.ui===8){
    this.router.navigate(['/admin/edit-task', id]);
    }
    else{
      this.router.navigate(['superadmin/edit-task', id]);
    }
  }

  onView(id: number): void {
    
    if(this.ui===8){
    this.router.navigate(['/admin/viewtask', id]);
    }
    else{
      this.router.navigate(['superadmin/viewtask', id]);
    }
  }

  onDelete(id: number): void {
    const deletedByStr = localStorage.getItem('empid');
    if (!deletedByStr) return;
    const deletedBy = Number(deletedByStr);
    if (isNaN(deletedBy)) return;

    this.taskService.deleteTask(id, deletedBy).subscribe({
      next: () => this.searchTasks(),
      error: (err) => console.error('Error deleting task', err)
    });
  }

  onAdd(): void {
    if(this.ui===8){
    this.router.navigate(['/admin/addtask']);
    }
    else{
      this.router.navigate(['superadmin/addtask']);
    }
  }

  // Optional: Pagination controls
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
