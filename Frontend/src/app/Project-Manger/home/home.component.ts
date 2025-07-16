import { Component, OnInit } from '@angular/core';
import { ProjectService, ProjectOut } from '../../Admin/services/projects.service';
import { TaskService, Task } from '../../Admin/services/tasks.service';
import { EmployeesService, Employee } from '../../Admin/services/employees.service';

type TaskStatus = 'Done' | 'Ongoing' | 'Pending';
type TaskPriority = 'High' | 'Medium' | 'Low';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
  standalone: false
})
export class HOMEComponent implements OnInit {

  projects: ProjectOut[] = [];
  selectedProject: ProjectOut | null = null;
  employees: Employee[] = [];

  allTasks: Task[] = [];
  tasks: {
    title: string;
    project_id: number;
    assignedTo: string;
    priority: TaskPriority;
    status: TaskStatus | string;
    dueDate: Date;
  }[] = [];

  recentTasks: {
    title: string;
    assignedTo: string;
    priority: TaskPriority;
    status: string;
    dueDate: Date;
  }[] = [];

  pieChartData: any;
  barChartData: any;

  constructor(
    private projectService: ProjectService,
    private taskService: TaskService,
    private employeeService: EmployeesService
  ) {}

  ngOnInit(): void {
    const empId = localStorage.getItem('empid');
    if (empId) {
      console.log(empId)
      this.fetchProjectsManagedByEmployee(+empId);
      console.log(this.employees)
    }

this.fetchAllEmployees();


    
  }

  fetchProjectsManagedByEmployee(empId: number): void {
    this.projectService.getProjectsByManager(empId).subscribe({
      next: (res) => {
        this.projects = res;
        this.selectedProject = this.projects.length > 0 ? this.projects[0] : null;
        this.fetchAllEmployees(); // ensure employees loaded before fetching tasks
      },
      error: (err) => {
        console.error('Failed to load projects for manager:', err);
      }

  
    });
  }
   fetchAllTasks(): void {
    this.taskService.getAllTasks().subscribe({
      next: (res) => {
        this.allTasks = res;

        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const managedProjectIds = this.projects.map(p => p.ProjectId);

        const recentRawTasks = this.allTasks.filter(task => {
          const createdDate = task.CreatedOn ? new Date(task.CreatedOn) : null;
          return (
            createdDate &&
            createdDate > oneDayAgo &&
            managedProjectIds.includes(task.ProjectId)
          );
        });

        this.recentTasks = recentRawTasks.map(task => {
          const employee = this.employees.find(e => e.emp_id === task.AssignedTo);
          return {
            title: task.Name,
            assignedTo: employee ? employee.name : 'Unassigned',
            priority: task.Priority as TaskPriority,
            status: task.Status,
            dueDate: new Date(task.Deadline)
          };
        });

        this.tasks = this.allTasks.map(task => {
          const employee = this.employees.find(e => e.emp_id === task.AssignedTo);
          return {
            title: task.Name,
            project_id: task.ProjectId,
            assignedTo: employee ? employee.name : 'Unassigned',
            priority: task.Priority as TaskPriority,
            status: task.Status,
            dueDate: new Date(task.Deadline)
          };
        });

        this.updateChart();
      },
      error: (err) => {
        console.error('Error fetching tasks:', err);
      }
    });
  }

  fetchAllEmployees(): void {
    this.employeeService.getAllEmployees().subscribe({
      next: (res) => {
        this.employees = res;
        this.fetchAllTasks(); // now fetch tasks
      },
      error: (err) => {
        console.error('Failed to load employees:', err);
      }
    });
  }

 

  barChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false,
        labels: {
          font: {
            size: 14,
            weight: 'bold'
          }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#000000' }
      },
      y: {
        ticks: { color: '#000000' }
      }
    }
  };

  updateChart(): void {
    if (!this.selectedProject) return;

    const projectTasks = this.tasks.filter(
      t => t.project_id === this.selectedProject!.ProjectId
    );

    const statusMap: Record<string, TaskStatus> = {
      'In Progress': 'Ongoing',
      'Completed': 'Done',
      'Pending': 'Pending',
      'Ongoing': 'Ongoing',
      'Done': 'Done'
    };

    const countByStatus: Record<TaskStatus, number> = { Done: 0, Ongoing: 0, Pending: 0 };
    const ongoingPriorities: Record<TaskPriority, number> = { High: 0, Medium: 0, Low: 0 };

    projectTasks.forEach(task => {
      const normalizedStatus = statusMap[task.status] || 'Pending';
      countByStatus[normalizedStatus]++;
      if (normalizedStatus === 'Ongoing') {
        ongoingPriorities[task.priority]++;
      }
    });

    this.pieChartData = {
      labels: ['Done', 'Ongoing', 'Pending'],
      datasets: [{
        data: [countByStatus.Done, countByStatus.Ongoing, countByStatus.Pending],
        backgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
        hoverBackgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
      }]
    };

    this.barChartData = {
      labels: ['High', 'Medium', 'Low'],
      datasets: [{
        label: 'Ongoing Task Priority',
        backgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
        hoverBackgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
        data: [ongoingPriorities.High, ongoingPriorities.Medium, ongoingPriorities.Low]
      }]
    };
  }
}
