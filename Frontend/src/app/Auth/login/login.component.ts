import { Component } from '@angular/core';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms';
import { Router } from '@angular/router';
import { UserRoleService } from '../../services/Service/user.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
  standalone: false
})
export class LoginComponent {
  showPassword: boolean = false;
  loginError: string | undefined;

  loginForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)])
  });

  constructor(
    private fb: FormBuilder,
    private userService: UserRoleService,
    private router: Router
  ) {}

  togglePasswordVisibility() {
    this.showPassword = !this.showPassword;
  }

  onSubmit() {
    if (this.loginForm.valid) {
      const { email, password } = this.loginForm.value;

      this.userService.login(email!, password!).subscribe({
        next: (res: any) => {
          this.userService.storeToken(res.access_token);  // Store and decode token

          const user = this.userService.getUser();
          const roleId = user?.role_id; // ✅ Correct usage

          console.log('Decoded Role ID:', roleId);

          // Optional: Store additional info
          if (user) {
            localStorage.setItem('companyId', user.company_id?.toString() || '');
            localStorage.setItem('email', user.email || '');
            localStorage.setItem('userid', user.user_id?.toString() || '');
          }

          // Role-based routing
          switch (roleId) {
            case 8:
              this.router.navigate(['/admin']);
              break;
            case 10:
              this.router.navigate(['/employee']);
              break;
            case 11:
              this.router.navigate(['/project-manager']);
              break;
            case 12:
              this.router.navigate(['/superadmin']);
              break;
            default:
              this.loginError = 'Unauthorized role access.';
          }
        },
        error: (err) => {
          this.loginError = err.error?.detail || 'Login failed.';
        }
      });
    } else {
      this.loginForm.markAllAsTouched();
    }
  }
}
