import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { NgForm } from '@angular/forms';
import { Employee, EmployeesService, RoleOption } from '../../../services/employees.service';
import { UserRegistration, UserRoleService } from '../../../../services/Service/user.service';

@Component({
  selector: 'app-add',
  standalone: false,
  templateUrl: './add.component.html',
  styleUrl: './add.component.css'
})
export class AddComponent implements OnInit {
  kl = false;
  ui = Number(localStorage.getItem('roleid'));

  @ViewChild('employeeForm') employeeForm!: NgForm;

  employee: Partial<Employee>& { password?: string } = {
    name: '',
    role_id: 0,
    phone: '',
    address: '',
    email: '',
    description: '',
    EmployeeImage: '',
    ImagePath: '',
    ImageUrl: '',
    password: '' // ✅ Add this line
  };

  selectedFiles: File[] = [];
  documentURLs: string[] = [];
  roles: RoleOption[] = [];

  constructor(
    private employeesService: EmployeesService,
    private router: Router,
    private userRoleService: UserRoleService // ✅ Added UserRoleService
  ) {}

  ngOnInit(): void {
    this.loadRoles();
    if (this.ui === 8) {
      this.kl = true;
    }
  }

  onFilesSelected(event: any): void {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      this.selectedFiles = [file];
      this.employee.EmployeeImage = file.name;

      const reader = new FileReader();
      reader.onload = (e: any) => {
        const base64Data = e.target.result;
        this.employee.ImageUrl = base64Data;
        this.documentURLs = [base64Data];
      };
      reader.readAsDataURL(file);
    }
  }

  loadRoles(): void {
    this.employeesService.getRoleOptions().subscribe({
      next: (data) => {
        this.roles = data
          .filter((r: any) => r.Role !== 'SuperAdmin')
          .map((r: any) => ({
            role_id: r.RoleId,
            role: r.Role
          }));
      },
      error: (err) => {
        console.error('Failed to load roles', err);
      }
    });
  }
  showPassword: boolean = false;

togglePasswordVisibility(): void {
  this.showPassword = !this.showPassword;
}


  onSubmit(form: NgForm) {
    if (form.invalid) {
      form.control.markAllAsTouched();
      return;
    }

    const company_id = localStorage.getItem('companyId');
    const created_by = localStorage.getItem('empid');

    if (!company_id || !created_by) {
      alert('Missing company or user ID.');
      return;
    }

    this.employee.company_id = Number(company_id);
    this.employee.created_by = Number(created_by);

    console.log('ImageUrl being sent:', this.employee.ImageUrl);

    this.employeesService.createEmployee(this.employee).subscribe({
      next: (res: any) => {
        alert('Employee added successfully');

        // ✅ Create user after employee is added
        const userPayload: UserRegistration = {
          user_id: 0, // let backend generate
          email: this.employee.email || '',
          password: this.employee.password||'', // can replace with form input or random gen
          role_id: this.employee.role_id || 0,
          created_by: Number(created_by),
          is_active: true,
          company_id: Number(company_id)
        };

        this.userRoleService.registerUser(userPayload).subscribe({
          next: () => {
            alert('User account created successfully');
            this.redirect();
          },
          error: (userErr) => {
            console.error('User creation failed', userErr);
            alert('Employee created, but user account creation failed.');
            this.redirect();
          }
        });
      },
      error: (err) => {
        console.error('Error adding employee:', err);
        alert('Failed to add employee: ' + JSON.stringify(err.error));
      }
    });
  }

  cancel() {
    this.redirect();
  }

  redirect() {
    if (this.ui === 8) {
      this.router.navigate(['/admin/employee']);
    } else {
      this.router.navigate(['/superadmin/Employee']);
    }
  }

  getError(controlName: string): string | null {
    const control = this.employeeForm?.controls[controlName];
    if (!control || !control.errors || !(control.dirty || control.touched)) {
      return null;
    }

    if (control.errors['required']) {
      return `${this.capitalize(controlName)} is required.`;
    }
    if (control.errors['minlength']) {
      const requiredLength = control.errors['minlength'].requiredLength;
      return `${this.capitalize(controlName)} must be at least ${requiredLength} characters.`;
    }
    if (control.errors['pattern'] && controlName === 'phone') {
      return `Phone must be 10 digits.`;
    }

    return null;
  }

  private capitalize(text: string) {
    return text.charAt(0).toUpperCase() + text.slice(1);
  }
}
