import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-profile',
  standalone: false,
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css'
})
export class ProfileComponent implements OnInit {
  empId = '';
  name = '';
  phone = '';
  address = '';
  description = '';
  role='';
  email='';
  employeeUrl='';
  ui=Number(localStorage.getItem('roleid'))
  
 constructor(private router: Router){}
  ngOnInit(): void {
    this.empId = localStorage.getItem('empid') || '';
    this.name = localStorage.getItem('name') || '';
    this.phone = localStorage.getItem('phone') || '';
    this.address = localStorage.getItem('address') || '';
    this.description = localStorage.getItem('description') || '';
    this.role= localStorage.getItem('role')||'';
    this.email=localStorage.getItem('email')||' ';
    this.employeeUrl = localStorage.getItem('imageurl') || '';

  }
  onEdit() {
  // Navigate to an edit page or open a form/modal
  if(this.ui===8){
     this.router.navigate(['/admin/editprofile']);
  }
  else{
     this.router.navigate(['/superadmin/Editprofile']);
  } // example route
}


}
