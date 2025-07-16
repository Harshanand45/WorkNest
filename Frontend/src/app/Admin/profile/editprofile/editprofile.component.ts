import { Component, OnInit, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { Router } from '@angular/router';
import { EmployeesService, Employee } from '../../services/employees.service';

@Component({
  selector: 'app-editprofile',
  templateUrl: './editprofile.component.html',
  styleUrls: ['./editprofile.component.css'],
  standalone:false
})
export class EditprofileComponent implements OnInit {
  @ViewChild('editForm') editForm!: NgForm;

  empId!: number;
 ui=Number(localStorage.getItem('roleid'))
  name: string = '';
  email: string = '';
  phone: string = '';
  address: string = '';
  description: string = '';
  imagePreview: string = '';
  employeeImageBase64: string = '';
  imagePath: string = '';
  updatedBy: number = 0;

  constructor(private empService: EmployeesService, private router: Router) {}

  ngOnInit(): void {
    const empIdStr = localStorage.getItem('empid');
    if (!empIdStr) {
      alert('No employee ID found in local storage.');
  
      this.router.navigate(['/login']);
      return;
    }

    this.empId = Number(empIdStr);
    this.updatedBy = this.empId;

    this.empService.getAllEmployees().subscribe({
      next: (employees) => {
        const found = employees.find(e => e.emp_id === this.empId);
        if (found) {
          this.name = found.name || '';
          this.email = found.email || '';
          this.phone = found.phone || '';
          this.address = found.address || '';
          this.description = found.description || '';
          this.imagePreview = found.ImageUrl || '';
          this.employeeImageBase64 = found.EmployeeImage || '';
          this.imagePath = found.ImagePath || '';
        } else {
          alert('Employee not found.');
          this.router.navigate(['/login']);
        }
      },
      error: () => {
        alert('Error fetching employee data.');
        this.router.navigate(['/login']);
      }
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      const reader = new FileReader();

      reader.onload = () => {
        const base64 = reader.result as string;
        this.employeeImageBase64 = base64;
        this.imagePreview = base64;
        this.imagePath = '';
      };

      reader.readAsDataURL(file);
    }
  }

  onSubmit(): void {
  if (this.editForm.invalid) {
    this.editForm.control.markAllAsTouched();
    return;
  }

  const payload: any = {
    phone: this.phone,
    address: this.address,
    description: this.description,
    updated_by: this.updatedBy,
    ImagePath: this.imagePath,
    EmployeeImage:this.employeeImageBase64,
    ImageUrl:this.imagePreview
    
  };

  // Only include base64 image if it's valid (starts with data:image/)
  if (this.employeeImageBase64 && this.employeeImageBase64.startsWith('data:image/')) {
    payload.EmployeeImage = this.employeeImageBase64;
    payload.ImageUrl = this.imagePreview;
  }

  this.empService.updateEmployee(this.empId, payload).subscribe({
    next: () => {
      alert('Profile updated successfully!');
      if(this.ui===8){
      this.router.navigate(['/admin/profile']);
      }
      else{
        this.router.navigate(['/superadmin/Profile']);
      }
        
      

    },
    error: (err) => {
      console.error('Error:', err);
      alert('Failed to update profile.');
    }
  });
}

}
