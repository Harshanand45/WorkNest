import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ProjectService } from '../../services/projects.service';
import { EmployeesService } from '../../services/employees.service';

@Component({
  selector: 'app-project',
  templateUrl: './project.component.html',
  styleUrls: ['./project.component.css'],
  standalone: false
})
export class ProjectComponent implements OnInit {
  projects: any[] = [];
  employees: any[] = [];
  employeeMap: { [key: number]: string } = {};
  ui=Number(localStorage.getItem('roleid'))

  // Filters & Pagination
  selectedManagerId: number | null = null;
  filterName: string = '';
  selectedStatus: string | null = null;
  statuses: string[] = ['Not Started', 'In Progress', 'Completed', 'On Hold'];

  currentPage: number = 1;
  pageLimit: number = 5;
  totalPages: number = 0;
  totalRecords: number = 0;

  constructor(
    private projectService: ProjectService,
    private employeeService: EmployeesService,
    private router: Router
  ) {}

  ngOnInit(): void {
    const companyId = Number(localStorage.getItem('companyId'));
    if (!companyId) {
      alert('Company ID missing in local storage.');
      return;
    }

    // Load employees excluding those with role_id === 8
    this.employeeService.getAllEmployees().subscribe({
      next: (emps) => {
        this.employees = emps.filter(emp => emp.company_id === companyId && emp.role_id !== 8);
        this.employeeMap = {};
        for (const emp of this.employees) {
          this.employeeMap[emp.emp_id] = emp.name;
        }
        this.loadPaginatedProjects(); // Load projects after loading employees
      },
      error: () => {
        alert('Failed to load employees.');
      }
    });
  }

  loadPaginatedProjects(): void {
    const companyId = Number(localStorage.getItem('companyId'));
    if (!companyId) {
      alert('Company ID missing.');
      return;
    }

    const filterPayload: any = {
      page: this.currentPage,
      PageLimit: this.pageLimit,
      project_manager: this.selectedManagerId || undefined,
      name: this.filterName?.trim() || undefined,
      status: this.selectedStatus || undefined
    };

    this.projectService.getPaginatedProjects(filterPayload).subscribe({
      next: (response) => {
        const filtered = (response.data || []).filter((p: any) => p.CompanyId === companyId);
        this.projects = filtered;
        this.totalPages = filtered.length === 0 ? 0 : response.total_pages || 1;
        this.totalRecords = response.total_records || 0;  // optional if API provides it
      },
      error: () => {
        alert('Failed to load paginated projects.');
      }
    });
  }

  getProjectManagerName(empId: number): string {
    return this.employeeMap[empId] || 'Unknown';
  }

  editProject(id: number): void {
    if(this.ui===8){
    this.router.navigate(['/admin/editpro', id]);
    }
    else{
       this.router.navigate(['/superadmin/editpro', id]);
    }
  }

  viewProject(id: number): void {
   if(this.ui===8){
    this.router.navigate(['/admin/viewproject', id]);
    }
    else{
       this.router.navigate(['/superadmin/viewproject', id]);
    }
  }

  deleteProject(id: number): void {
    const deletedBy = Number(localStorage.getItem('empid'));
    if (!deletedBy) {
      alert('Invalid session. Please login again.');
      return;
    }

    if (confirm('Are you sure you want to delete this project?')) {
      this.projectService.deleteProject(id, deletedBy).subscribe({
        next: () => {
          this.projects = this.projects.filter(p => p.ProjectId !== id);
          alert('Project deleted successfully.');
          this.loadPaginatedProjects();
        },
        error: () => {
          alert('Failed to delete project.');
        }
      });
    }
  }

  addProject(): void {
    if(this.ui===8){
    this.router.navigate(['/admin/add']);
    }
    else{
       this.router.navigate(['/superadmin/add']);
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadPaginatedProjects();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadPaginatedProjects();
    }
  }

  clearFilter(): void {
    this.selectedManagerId = null;
    this.filterName = '';
    this.selectedStatus = null;
    this.currentPage = 1;
    this.loadPaginatedProjects();
  }
}
