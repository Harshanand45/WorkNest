import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { NgForm } from '@angular/forms';
import { Task, TaskService } from '../../../Admin/services/tasks.service';
import { Timelog, TimeLogService } from '../../../Admin/services/timelog.service';
import { ProjectService, ProjectOut } from '../../../Admin/services/projects.service';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-taskview',
  templateUrl: './taskview.component.html',
  styleUrls: ['./taskview.component.css'],
  standalone: false
})
export class TaskviewComponent implements OnInit {
  task: Task | undefined;
  projectName: string = '';
  isEmployee = true;

  @ViewChild('taskForm') taskForm!: NgForm;

  log = {
    date: '',
    hoursWorked: 0,
    minutesWorked: 0,
    description: ''
  };

  showLogForm: boolean = false;
  prevStatus: string = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private taskService: TaskService,
    private timeLogService: TimeLogService,
    private projectService: ProjectService
  ) {}

  ngOnInit(): void {
    const taskId = Number(this.route.snapshot.paramMap.get('id'));
    if (isNaN(taskId)) {
      console.error('Invalid Task ID');
      return;
    }

    forkJoin({
      projects: this.projectService.getAllProjects(),
      tasks: this.taskService.getAllTasks()
    }).subscribe({
      next: ({ projects, tasks }) => {
        this.task = tasks.find(t => t.TaskId === taskId);

        if (this.task) {
          const project = projects.find(p => p.ProjectId === this.task?.ProjectId);
          this.projectName = project ? project.Name : 'N/A';
          this.prevStatus = this.task.Status;
        }
      },
      error: (err) => {
        console.error('Error loading data', err);
      }
    });
  }

  onStatusChange() {
    if (!this.task) return;

    const currentStatus = this.task.Status;

    // Show log form only when:
    // - Going from Pending → InProgress or Completed
    // - Going from InProgress → Completed
    if (
      (this.prevStatus === 'Pending' && (currentStatus === 'In Progress' || currentStatus === 'Completed')) ||
      (this.prevStatus === 'In Progress' && currentStatus === 'Completed')
    ) {
      this.showLogForm = true;
    } else {
      this.showLogForm = false;
    }
  }

  preventDecimal(event: KeyboardEvent) {
    if (event.key === '.' || event.key === ',') {
      event.preventDefault();
    }
  }

  goBack() {
    history.back();
  }

  saveAll() {
    if (!this.task) return;

    const updatedBy = Number(localStorage.getItem('empid'));

    // Trigger validation
    if (this.taskForm) {
      this.taskForm.control.markAllAsTouched();
    }

    // Log validation only if task is marked as Completed
    if (this.task.Status === 'Completed') {
      const invalid =
        !this.log.date ||
        (!this.log.hoursWorked && !this.log.minutesWorked) ||
        !this.log.description.trim();

      if (invalid || this.taskForm.invalid) {
        alert('Please fill in all required log time details before completing the task.');
        return;
      }
    }

    // Task update
    this.taskService.updateTask(this.task.TaskId, {
      Status: this.task.Status,
      UpdatedBy: updatedBy
    }).subscribe({
      next: () => {
        // If completed, log time
        if (this.task?.Status === 'Completed') {
          const log: Timelog = {
            empId: this.task.AssignedTo ?? 0,
            taskId: this.task.TaskId??0,
            date: this.log.date,
            companyId: Number(localStorage.getItem('companyId')),
            description: this.log.description,
            minutesSpent: this.log.minutesWorked,
            hoursSpent: this.log.hoursWorked,
            createdBy: updatedBy
          };

          this.timeLogService.addLog(log).subscribe({
            next: () => {
              alert('Task updated and time logged successfully!');
              this.router.navigate(['/employee/task']);
            },
            error: (err) => {
              console.error('Log time failed', err);
              alert('Task updated, but failed to log time.');
            }
          });
        } else {
          alert('Task status updated successfully!');
          this.router.navigate(['/employee/task']);
        }
      },
      error: (err) => {
        console.error('Task update failed:', err);
        alert('Failed to update task.');
      }
    });
  }
}
