import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RolesService, Role } from '../../Admin/services/roles.service';

@Component({
  selector: 'app-role',
  templateUrl: './roles.component.html',
  styleUrls: ['./roles.component.css'],
  standalone:false
})
export class RolesComponent implements OnInit {
  roles: Role[] = [];
  roleForm!: FormGroup;

  currentPage: number = 1;
  totalPages: number = 1;
  pageSize: number = 10;

  isEditMode = false;
  editingRoleId: number | null = null;

  isLoading = false;
  loggedInUserId = 1;
  companyId = Number(localStorage.getItem('companyId')) || 0;

  @ViewChild('closeModalBtn') closeModalBtn!: ElementRef;

  constructor(private fb: FormBuilder, private roleService: RolesService) {}

  ngOnInit(): void {
    this.initForm();
    this.loadRoles();
  }

  initForm(): void {
    this.roleForm = this.fb.group({
      role: ['', Validators.required],
    });
  }

  loadRoles(): void {
    this.isLoading = true;
    this.roleService.getPaginatedRoles({ page: this.currentPage, PageLimit: this.pageSize }).subscribe({
      next: (res) => {
        this.roles = res.data;
        this.totalPages = res.total_pages || 1;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error loading roles:', err);
        this.isLoading = false;
      }
    });
  }

  openCreateModal(): void {
    this.isEditMode = false;
    this.editingRoleId = null;
    this.roleForm.reset();
  }

  editRole(role: Role): void {
    this.isEditMode = true;
    this.editingRoleId = role.role_id;
    this.roleForm.patchValue({
      role: role.role || ''
    });
  }

  submitRole(): void {
    if (this.roleForm.invalid) return;

    const payload = {
      role: this.roleForm.value.role,
      company_id: this.companyId,
      updated_by:2,
    };

    if (this.isEditMode && this.editingRoleId !== null) {
      this.roleService.updateRole(this.editingRoleId, payload).subscribe({
        next: () => {
          alert('Role updated');
          this.loadRoles();
          this.closeModalBtn.nativeElement.click();
        },
        error: (err) => alert(err.error?.detail || 'Error updating role')
      });
    } else {
      const createPayload = {
        ...payload,
        created_by: 2,
        is_active: true
      };
      this.roleService.createRole(createPayload).subscribe({
        next: () => {
          alert('Role created');
          this.loadRoles();
          this.closeModalBtn.nativeElement.click();
        },
        error: (err) => alert(err.error?.detail || 'Error creating role')
      });
    }
  }

  deleteRole(roleId: number): void {
    if (confirm('Are you sure you want to delete this role?')) {
      this.roleService.deleteRole(roleId, 2).subscribe({
        next: () => {
          alert('Role deleted');
          this.loadRoles();
        },
        error: (err) => alert(err.error?.detail || 'Error deleting role')
      });
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadRoles();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadRoles();
    }
  }
}
