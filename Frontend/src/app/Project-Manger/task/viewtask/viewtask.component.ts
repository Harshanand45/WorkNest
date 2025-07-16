import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Task, TaskService } from '../../../Admin/services/tasks.service';
import { EmployeesService, Employee } from '../../../Admin/services/employees.service';
import { ProjectService, ProjectOut } from '../../../Admin/services/projects.service';

@Component({
  selector: 'app-viewtask',
  templateUrl: './viewtask.component.html',
  styleUrls: ['./viewtask.component.css'],
  standalone: false
})
export class ViewtaskComponent implements OnInit {
  task: Task | undefined;
  loading: boolean = true;
  error: string = '';

  employees: Employee[] = [];
  projects: ProjectOut[] = [];

  assignedEmployeeName: string = '';
  projectName: string = '';

  constructor(
    private route: ActivatedRoute,
    private taskService: TaskService,
    private employeeService: EmployeesService,
    private projectService: ProjectService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (isNaN(id)) {
      this.error = 'Invalid Task ID';
      this.loading = false;
      return;
    }

    // Step 1: Get all employees
    this.employeeService.getAllEmployees().subscribe({
      next: (employees) => {
        this.employees = employees;

        // Step 2: Get all projects
        this.projectService.getAllProjects().subscribe({
          next: (projects) => {
            this.projects = projects;

            // Step 3: Get all tasks
            this.taskService.getAllTasks().subscribe({
              next: (tasks) => {
                this.task = tasks.find(t => t.TaskId === id);
                if (!this.task) {
                  this.error = 'Task not found.';
                  this.loading = false;
                  return;
                }

                const assignedEmployee = this.employees.find(emp => emp.emp_id === this.task?.AssignedTo);
                this.assignedEmployeeName = assignedEmployee ? assignedEmployee.name : 'Unassigned';

                const project = this.projects.find(p => p.ProjectId === this.task?.ProjectId);
                this.projectName = project ? project.Name : 'Unknown Project';

                this.loading = false;
              },
              error: (err) => {
                console.error('Error fetching task:', err);
                this.error = 'Failed to load task.';
                this.loading = false;
              }
            });
          },
          error: (err) => {
            console.error('Error loading projects', err);
            this.error = 'Failed to load projects.';
            this.loading = false;
          }
        });
      },
      error: (err) => {
        console.error('Error loading employees', err);
        this.error = 'Failed to load employees.';
        this.loading = false;
      }
    });
  }
}
