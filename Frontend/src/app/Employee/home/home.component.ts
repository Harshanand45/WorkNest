import { Component, OnInit } from '@angular/core';
import { TaskService, Task } from '../../Admin/services/tasks.service';
import { ProjectService, ProjectOut } from '../../Admin/services/projects.service';

@Component({
  selector: 'app-home',
  standalone: false,
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  pieChartData: any;
  pieChartOptions: any;

  barData: any;
  barOptions: any;

  recentTasks: Task[] = [];
  allProjects: ProjectOut[] = [];

  constructor(
    private taskService: TaskService,
    private projectService: ProjectService
  ) {}

  ngOnInit() {

    const empId = Number(localStorage.getItem('empid'));
    console.log('Employee ID:', empId);

    if (!empId) return;

    // First fetch all projects
    this.projectService.getAllProjects().subscribe((projects: ProjectOut[]) => {
      this.allProjects = projects;

      // Then fetch tasks for the employee
      this.taskService.getTasksByEmployee(empId).subscribe((tasks: Task[]) => {
        console.log('Tasks from API:', tasks);

        // Map project names to tasks
        tasks.forEach(task => {
          const project = this.allProjects.find(p => p.ProjectId === task.ProjectId);
          (task as any).ProjectName = project ? project.Name : 'N/A';
        });

        // Set recent tasks
        this.recentTasks = tasks.slice(0, 3);

        // Prepare chart data
        const statusCount: { [key: string]: number } = { Ongoing: 0, Completed: 0, Pending: 0 };
        const priorityCount: { [key: string]: number } = { High: 0, Medium: 0, Low: 0 };

        tasks.forEach(task => {
          if (statusCount.hasOwnProperty(task.Status)) statusCount[task.Status]++;
          if (priorityCount.hasOwnProperty(task.Priority)) priorityCount[task.Priority]++;
        });

        this.pieChartData = {
          labels: ['Ongoing', 'Completed', 'Pending'],
          datasets: [
            {
              data: [
                statusCount['Ongoing'],
                statusCount['Completed'],
                statusCount['Pending']
              ],
              backgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
              hoverBackgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
              borderColor: '#fff',
              borderWidth: 2
            }
          ]
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
              labels: {
                color: '#111',
                font: {
                  size: 14,
                  weight: 'bold'
                }
              }
            },
            tooltip: {
              callbacks: {
                label: (context: any) => {
                  const label = context.label || '';
                  const value = context.raw;
                  return `${label}: ${value}`;
                }
              }
            }
          },
          responsive: true,
          maintainAspectRatio: false
        };

        this.barData = {
          labels: ['High', 'Medium', 'Low'],
          datasets: [
            {
              backgroundColor: ['#A3D2CA', '#F6BD60', '#F7A072'],
              data: [
                priorityCount['High'],
                priorityCount['Medium'],
                priorityCount['Low']
              ]
            }
          ]
        };

        this.barOptions = {
          plugins: {
            title: {
              display: true,
              text: 'Priority of Task',
              font: { size: 18 }
            },
            legend: { display: false },
            datalabels: {
              anchor: 'end',
              align: 'top',
              color: '#000',
              font: { weight: 'bold' }
            }
          },
          scales: {
            y: { beginAtZero: true }
          }
        };
      });
    });
  }
}
