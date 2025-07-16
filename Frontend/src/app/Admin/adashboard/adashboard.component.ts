import { Component, HostListener, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Employee, EmployeesService } from '../services/employees.service';

@Component({
  selector: 'app-adashboard',
  standalone: false,
  templateUrl: './adashboard.component.html',
  styleUrl: './adashboard.component.css'
})
export class AdashboardComponent implements OnInit {


  sidebarClosed = false;  
  employeeName: string = '';
  employeeUrl: string = 'https://cdn-icons-png.flaticon.com/512/149/149071.png'; // default fallback image
  employeeroleid: number = 0;
 

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
          this.employeeroleid=matchedEmployee.role_id

          // Set profile image if available
          if (matchedEmployee.ImageUrl) {
            this.employeeUrl = matchedEmployee.ImageUrl;
            localStorage.setItem('imageurl', matchedEmployee.ImageUrl);
          }

          // Set other user data in localStorage
          localStorage.setItem('name', matchedEmployee.name || '');
          localStorage.setItem('empid', matchedEmployee.emp_id?.toString() || '');
          localStorage.setItem('roleid',matchedEmployee.role_id.toString())
          localStorage.setItem('phone', matchedEmployee.phone?.toString() || '');
          localStorage.setItem('address', matchedEmployee.address || '');
          localStorage.setItem('description', matchedEmployee.description || '');
        

        } else {
          console.warn('No matching employee found for email:', email);
        }
      },
      error: (error) => {
        console.error('Error fetching employees:', error);
        
      }
    });

    this.checkScreenSize();
  }
 ui=Number(localStorage.getItem('roleid'))
  profile(): void {
    
      if(this.ui===8){
        this.router.navigate(['/admin/profile']);
        }
        else{
          this.router.navigate(['/superadmin/Profile']);
        }
  }

    @HostListener('window:resize', [])
    onResize() {
      this.checkScreenSize(); // Update state on resize
    }

    checkScreenSize() {
      const screenWidth = window.innerWidth;
      this.sidebarClosed = screenWidth <= 991;
    }
}
