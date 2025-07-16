import { Component } from '@angular/core';
import { Employee, EmployeesService } from '../../Admin/services/employees.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent {
  sidebarClosed = false;  
  employeeName: string = '';
  employeeUrl: string = 'https://cdn-icons-png.flaticon.com/512/149/149071.png'; // default fallback image

  constructor(
    private workService: EmployeesService,
    private router: Router
  ) {}

  ngOnInit(): void {
    const email = localStorage.getItem('email');
    if (!email) {
      console.warn('No email found in localStorage');
      return;
    }

    this.workService.getAllEmployees().subscribe({
      next: (employees: Employee[]) => {
        const matchedEmployee = employees.find(
          emp => emp.email?.toLowerCase() === email.toLowerCase()
        );

        if (matchedEmployee) {
          this.employeeName = matchedEmployee.name || 'User';

          // Set profile image if available
          if (matchedEmployee.ImageUrl) {
            this.employeeUrl = matchedEmployee.ImageUrl;
            localStorage.setItem('imageurl', matchedEmployee.ImageUrl);
          }

          // Set other user data in localStorage
          localStorage.setItem('name', matchedEmployee.name || '');
          localStorage.setItem('empid', matchedEmployee.emp_id?.toString() || '');
          localStorage.setItem('phone', matchedEmployee.phone?.toString() || '');
          localStorage.setItem('address', matchedEmployee.address || '');
          localStorage.setItem('description', matchedEmployee.description || '');
          localStorage.setItem('employeeUrl',matchedEmployee.ImageUrl)

        } else {
          console.warn('No matching employee found for email:', email);
        }
      },
      error: (error) => {
        console.error('Error fetching employees:', error);
      }
    });
  }

  profile(): void {
    this.router.navigate(['/superadmin/profile']);
  }

}
