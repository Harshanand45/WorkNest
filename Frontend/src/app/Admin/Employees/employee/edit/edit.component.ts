import { Component, OnInit, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { EmployeesService, Employee, RoleOption } from '../../../services/employees.service';

@Component({
  selector: 'app-edit',
  standalone: false,
  templateUrl: './edit.component.html',
  styleUrl: './edit.component.css'
})
export class EditComponent implements OnInit {
  @ViewChild('employeeForm') employeeForm!: NgForm;
   
  employeeId!: number;
  employee: Partial<Employee> = {
    name: '',
    role_id: 0,
    phone: '',
    address: '',
    email: '',
    description: '',
    updated_by: 0, 
    EmployeeImage:'',
    ImagePath:'',
    ImageUrl:''
  };

  roles: RoleOption[] = [];

  constructor(
    private route: ActivatedRoute,
    private employeesService: EmployeesService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.employeeId = Number(this.route.snapshot.paramMap.get('id'));

    this.loadRoles();

    this.employeesService.getAllEmployees().subscribe({
      next: (employees) => {
        const found = employees.find(e => e.emp_id === this.employeeId);
        if (found) {
          this.employee = { ...found };
          // Set updated_by from localStorage empid
          const empid = localStorage.getItem('empid');
          this.employee.updated_by = empid ? Number(empid) : 0;
        } else {
          alert('Employee not found');
          this.router.navigate(['/admin/employee']);
        }
      },
      error: () => {
        alert('Error fetching employee data');
        this.router.navigate(['/admin/employee']);
      }
    });
  }

  loadRoles(): void {
    this.employeesService.getRoleOptions().subscribe({
      next: (data) => {
        this.roles = data.map((r: any) => ({
          role_id: r.RoleId,
          role: r.Role
        }));
      },
      error: (err) => {
        console.error('Failed to load roles', err);
      }
    });
  }

  getError(controlName: string): string | null {
    const control = this.employeeForm?.controls[controlName];
    if (!control || !control.errors || !(control.dirty || control.touched)) return null;

    if (control.errors['required']) return `${this.capitalize(controlName)} is required.`;
    if (control.errors['minlength']) return `${this.capitalize(controlName)} is too short.`;
    if (control.errors['pattern']) return `Invalid ${this.capitalize(controlName)}.`;

    return null;
  }

  private capitalize(text: string) {
    return text.charAt(0).toUpperCase() + text.slice(1);
  }
   selectedFile: File | null = null;
selectedFileName: string = '';
   hj=Number(localStorage.getItem('roleid'))
onFileSelected(event: Event): void {
  const input = event.target as HTMLInputElement;

  if (input.files && input.files.length > 0) {
    this.selectedFile = input.files[0];
    this.selectedFileName = this.selectedFile.name;

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;

      this.employee.ImageUrl = result;
      this.employee.EmployeeImage = result;  // ✅ correct base64 data
      this.employee.ImagePath = '';
    };

    reader.readAsDataURL(this.selectedFile);
  } else {
    this.selectedFile = null;
    this.selectedFileName = '';
    this.employee.ImageUrl = '';
    this.employee.EmployeeImage = '';  // optional reset
  }
}





  onSubmit() {
    if (this.employeeForm.invalid) {
      this.employeeForm.control.markAllAsTouched();
      return;
    }

    const updatedPayload = {
      name: this.employee.name,
      role_id: this.employee.role_id,
      phone: this.employee.phone,
      address: this.employee.address,
      email: this.employee.email,
      description: this.employee.description,
      updated_by: this.employee.updated_by || 0,
       EmployeeImage:this.employee.EmployeeImage,
       ImagePath: this.employee.ImagePath,
       ImageUrl: this.employee.ImageUrl
      
    };
    

    this.employeesService.updateEmployee(this.employeeId, updatedPayload).subscribe({
  next: () => {
    alert('Employee updated successfully!');
    if(this.hj===8){
    this.router.navigate(['/admin/employee']);
    }
    else{
      this.router.navigate(['/superadmin/Employee']);
    }
  },
  error: (err) => {
    console.error('Update employee error:', err);
    alert('Failed to update employee: ' + (err.error?.message || JSON.stringify(err.error) || err.message || 'Unknown error'));
  }
});

  }

  cancel() {
   if(this.hj===8){
    this.router.navigate(['/admin/employee']);
    }
    else{
      this.router.navigate(['/superadmin/Employee']);
    }
  }
}
