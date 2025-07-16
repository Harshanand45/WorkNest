import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { EmployeesService, RoleOption, Employee, PaginatedEmployeeResponse } from '../../services/employees.service';
import { UserRoleService } from '../../../services/Service/user.service';
declare var bootstrap: any;
@Component({
  selector: 'app-employee',
  templateUrl: './employee.component.html',
  styleUrls: ['./employee.component.css'],
  standalone: false
})
export class EmployeeComponent implements OnInit {
  employees: Employee[] = [];
  roles: RoleOption[] = [];

  // Filter and Pagination
  searchKeyword: string = '';
  selectedRoleId: string = '';
  currentPage: number = 1;
  pageLimit: number = 5;
  totalPages: number = 1;
  totalItems: number = 0;
  selectedAddress: string = '';

  openAddressModal(address: string): void {
    this.selectedAddress = address;
    const modalElement = document.getElementById('addressModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
  }

  constructor(private employeesService: EmployeesService, private router: Router,private userservice:UserRoleService) {}

  ngOnInit(): void {
    this.loadRoles();
    this.loadEmployees();
  }

  loadRoles(): void {
    this.employeesService.getRoleOptions().subscribe({
      next: (roleData) => {
        this.roles = roleData.map((r: any) => ({
          role_id: r.RoleId,
          role: r.Role
        }));
      },
      error: (err) => console.error('Error loading roles:', err)
    });
  }

  loadEmployees(): void {
    const companyIdStr = localStorage.getItem('companyId');
    const company_id = companyIdStr ? Number(companyIdStr) : null;

    if (!company_id) {
      console.error('Company ID not found in local storage.');
      return;
    }

    this.employeesService.getPaginatedEmployees({
      page: this.currentPage,
      page_limit: this.pageLimit,
      search: this.searchKeyword,
      role_id: this.selectedRoleId ? Number(this.selectedRoleId) : undefined,
      company_id
    }).subscribe({
      next: (res: PaginatedEmployeeResponse) => {
        this.employees = res.data.filter(emp => emp.role_id !== 12); // exclude role_id 8 if needed
        this.totalItems = res.total;
        this.totalPages = res.total_pages;
        if (this.totalPages === 0) this.currentPage = 0;
      },
      error: (err) => console.error('Error fetching employees:', err)
    });
  }

  clearFilters(): void {
    this.searchKeyword = '';
    this.selectedRoleId = '';
    this.currentPage = 1;
    this.loadEmployees();
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadEmployees();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadEmployees();
    }
  }

  getRoleName(roleId: number): string {
    const role = this.roles.find(r => r.role_id === roleId);
    return role ? role.role : 'Unknown Role';
  } 

   hj=Number(localStorage.getItem('roleid'))
  addEmployee(): void {
    if(this.hj===8){
    this.router.navigate(['/admin/addemp']);
    }
    else{
      this.router.navigate(['/superadmin/addemp']);
    }
   
  }

  editEmployee(empId: number): void {
     if(this.hj===8){  this.router.navigate(['/admin/editemp', empId]);
    }
    else{
      this.router.navigate(['/superadmin/editemp', empId]);
    }
        
  }

 deleteEmployee(empId: number): void {
  const deletedByStr = localStorage.getItem('empid');
  const deletedBy = deletedByStr ? Number(deletedByStr) : null;

  if (!deletedBy) {
    alert('User ID not found. Please log in again.');
    return;
  }

  if (confirm('Are you sure you want to delete this employee?')) {
    // Step 1: Delete from Users table
    this.userservice.deleteUser(empId, deletedBy).subscribe({
      next: (res) => {
        console.log('User deleted:', res.message);

        // Step 2: Delete from Employee table
        this.employeesService.deleteEmployee(empId, deletedBy).subscribe({
          next: () => {
            alert('Employee deleted successfully');
            this.loadEmployees(); // reload list
          },
          error: (err) => {
            console.error('Error deleting employee:', err);
            alert(err.error?.detail || 'Error deleting employee record');
          }
        });
      },
      error: (err) => {
        console.error('Error deleting user:', err);
        alert(err.error?.detail || 'Error deleting user record');
      }
    });
  }
}

}
