import { Component, OnInit } from '@angular/core';
import { Title } from 'chart.js';
import { CardModule } from 'primeng/card';
import { TableModule } from 'primeng/table';
import { DashboardService, ProjectOut, TaskOut } from '../../../services/dashboard.service';
import { Employee, WorkService } from '../../../services/work.service';
import { TaskService } from '../../../services/tasks.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-ahome',
  standalone: false,
  templateUrl: './ahome.component.html',
  styleUrl: './ahome.component.css'
})
export class AhomeComponent implements OnInit {
 ui=Number(localStorage.getItem('roleid'))
  pieChartData: any;
  pieChartOptions: any;
  barData: any;
  barOptions: any;
  allEmployees: Employee[] = [];
  recentTasks: (TaskOut & { assignedToName: string })[] = [];
  recentTask: TaskOut[] = [];

  constructor(
    private dashboardService: DashboardService,
    private workService: WorkService,
    private taskService: TaskService,
     private router: Router
  ) {}

  ngOnInit() {
    const companyId = localStorage.getItem('companyId');
    if (!companyId) {
      console.error('No companyId found in localStorage');
      return;
    }

    // Load employees and recent tasks (with employee names)
    this.loadRecentTasksWithNames();

    // Fetch and prepare project data (bar chart only)
    this.dashboardService.getAllProjects().subscribe({
      next: (projects: ProjectOut[]) => {
        const filteredProjects = projects.filter(p => p.CompanyId.toString() === companyId);
        // Instead of preparePieChart with projects, use task statuses for pie chart
        this.prepareBarChart(filteredProjects);
        this.loadTaskStatusPieChart(companyId);
      },
      error: (err) => {
        console.error('Error fetching projects', err);
      }
    });
  }

  isLoadingRecentTasks = false;

  loadRecentTasksWithNames(): void {
    this.workService.getAllEmployees().subscribe({
      next: (employees: Employee[]) => {
        this.allEmployees = employees;

        this.dashboardService.getRecentTasks().subscribe({
          next: (tasks: TaskOut[]) => {
            this.recentTasks = tasks.map(task => {
              const assignedId = Number(task.AssignedTo);
              const matchedEmp = employees.find(emp => emp.emp_id === assignedId);
              return {
                ...task,
                assignedToName: matchedEmp ? matchedEmp.name : 'Unassigned'
              };
            });
          },
          error: err => {
            console.error('Error fetching recent tasks:', err);
          }
        });
      },
      error: err => {
        console.error('Error fetching employees:', err);
      }
    });
  }

  loadTaskStatusPieChart(companyId: string): void {
    this.taskService.getAllTasks().subscribe({
      next: (tasks) => {
        // Filter tasks by companyId first
        const filteredTasks = tasks.filter(t => t.CompanyId.toString() === companyId);

        // Count task statuses
        const statusCounts: Record<string, number> = { InProgress: 0, Completed: 0, Pending: 0 };

        filteredTasks.forEach(task => {
          if (task.Status && task.Status in statusCounts) {
            statusCounts[task.Status]++;
          }
        });

        this.pieChartData = {
          labels: Object.keys(statusCounts),
          datasets: [{
            data: Object.values(statusCounts),
            backgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
            borderColor: '#fff',
            borderWidth: 2
          }]
        };

        this.pieChartOptions = {
          plugins: {
            title: {
              display: true,
              text: 'Task Status',
              font: { size: 18 }
            },
            legend: {
              position: 'bottom',
              labels: { font: { size: 14, weight: 'bold' } }
            },
            tooltip: {
              callbacks: {
                label: (context: any) => `${context.label}: ${context.raw}`
              }
            }
          },
          responsive: true,
          maintainAspectRatio: false
        };
      },
      error: err => {
        console.error('Error fetching tasks for pie chart:', err);
      }
    });
  }

  prepareBarChart(projects: ProjectOut[]) {
    const priorityCounts = { High: 0, Medium: 0, Low: 0 };

    projects.forEach(p => {
      if (p.Priority in priorityCounts) {
        priorityCounts[p.Priority]++;
      }
    });

    this.barData = {
      labels: Object.keys(priorityCounts),
      datasets: [{
        backgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
        data: Object.values(priorityCounts)
      }]
    };

    this.barOptions = {
      plugins: {
        title: { display: true, text: 'Priority of Projects', font: { size: 18 } },
        legend: { display: false },
        datalabels: { anchor: 'end', align: 'bottom', color: '#000', font: { weight: 'bold' } }
      },
      scales: { y: { beginAtZero: true } }
    };
  }
    onView(id: number): void {
    
    if(this.ui===8){
    this.router.navigate(['/admin/viewtask', id]);
    }
    else{
      this.router.navigate(['superadmin/viewtask', id]);
    }
  }


}
