import { Injectable } from '@angular/core';

export interface Employee {
  id: number;
  name: string;
  role: string;
  phone: string;
  address: string;
}

@Injectable({
  providedIn: 'root',
})
export class EmployeeService {
   employees: Employee[] = [
    {
      id: 1,
      name: 'John Doe',
      role: 'Developer',
      phone: '1234567890',
      address: '123 Main St, City',
    },
    {
      id: 2,
      name: 'Jane Smith',
      role: 'Designer',
      phone: '9876543210',
      address: '456 Elm St, Town',
    },
  ];

  private nextId: number = 3;

  constructor() {}

  // Get all employees
  getEmployees(): Employee[] {
    return [...this.employees];
  }

  // Get employee by ID
  getEmployeeById(id: number): Employee | undefined {
    return this.employees.find(emp => emp.id === id);
  }

  // Add a new employee
  addEmployee(employee: Omit<Employee, 'id'>): void {
    const newEmployee: Employee = {
      id: this.nextId++,
      ...employee,
    };
    this.employees.push(newEmployee);
  }

  // Update an existing employee
  updateEmployee(id: number, updatedEmployee: Omit<Employee, 'id'>): boolean {
    const index = this.employees.findIndex(emp => emp.id === id);
    if (index !== -1) {
      this.employees[index] = { id, ...updatedEmployee };
      return true;
    }
    return false;
  }

  // Delete an employee
  deleteEmployee(id: number): boolean {
    const initialLength = this.employees.length;
    this.employees = this.employees.filter(emp => emp.id !== id);
    return this.employees.length < initialLength;
  }
}
