import { Component, OnInit } from '@angular/core';
import * as XLSX from 'xlsx';
import * as FileSaver from 'file-saver';
import { Timelog, TimeLogService } from '../services/timelog.service';
import { EmployeesService, Employee } from '../services/employees.service';
import { TaskService, Task } from '../services/tasks.service';

@Component({
  selector: 'app-report',
  templateUrl: './report.component.html',
  styleUrls: ['./report.component.css'],
  standalone: false
})
export class ReportComponent implements OnInit {
  logs: Timelog[] = [];
  filteredLogs: Timelog[] = [];

  employees: Employee[] = [];
  tasks: Task[] = [];

  selectedEmpId: number | null = null;
  taskSearch: string = '';
  startDate: string = '';
  endDate: string = '';

  // Pagination
  currentPage: number = 1;
  itemsPerPage: number = 10;
  totalPages: number = 0;

  constructor(
    private timeLogService: TimeLogService,
    private employeesService: EmployeesService,
    private taskService: TaskService
  ) {}

  ngOnInit(): void {
    this.loadLogs();
    this.loadEmployees();
    this.loadTasks();
  }

  loadLogs(): void {
    this.timeLogService.getAllLogs().subscribe({
      next: (data) => {
        this.logs = data.map((log: any) => ({
          empId: log.EmpId,
          taskId: log.TaskId,
          date: log.Date,
          companyId: log.CompanyId,
          description: log.Description,
          hoursSpent: log.HoursSpent ?? 0,
          minutesSpent: log.MinutesSpent ?? 0,
          createdBy: log.CreatedBy ?? null
        }));
        this.applyFilters();
      },
      error: (err) => {
        console.error('Error loading logs:', err);
      }
    });
  }

  loadEmployees(): void {
    this.employeesService.getAllEmployees().subscribe({
      next: (data) => {
        this.employees = data.filter(emp => emp.role_id !== 8 && emp.role_id !== 11);
      },
      error: (err) => {
        console.error('Error loading employees:', err);
      }
    });
  }

  loadTasks(): void {
    this.taskService.getAllTasks().subscribe({
      next: (data) => {
        this.tasks = data;
      },
      error: (err) => {
        console.error('Error loading tasks:', err);
      }
    });
  }

  getEmployeeName(empId: number): string {
    const emp = this.employees.find(e => e.emp_id === empId);
    return emp ? emp.name : 'Unknown';
  }

  getTaskName(taskId: number): string {
    const task = this.tasks.find(t => t.TaskId === taskId);
    return task ? task.Name : 'Unknown Task';
  }

  getExpectedHours(taskId: number): string {
    const task = this.tasks.find(t => t.TaskId === taskId);
    return task?.ExptedHours !== undefined && task?.ExptedHours !== null
      ? task.ExptedHours.toString()
      : '-';
  }

  formatTime(hours?: number, minutes?: number): string {
    const safeHours = typeof hours === 'number' ? hours : 0;
    const safeMinutes = typeof minutes === 'number' ? minutes : 0;
    const h = safeHours.toString().padStart(2, '0') + 'h';
    const m = safeMinutes.toString().padStart(2, '0') + 'm';
    return `${h} ${m}`;
  }

  applyFilters(): void {
    const filtered = this.logs.filter(log => {
      const matchesEmployee = !this.selectedEmpId || log.empId === this.selectedEmpId;
      const taskName = this.getTaskName(log.taskId).toLowerCase();
      const matchesTask = !this.taskSearch || taskName.includes(this.taskSearch.toLowerCase());

      const logDate = new Date(log.date);
      const start = this.startDate ? new Date(this.startDate) : null;
      const end = this.endDate ? new Date(this.endDate) : null;
      const matchesDate = (!start || logDate >= start) && (!end || logDate <= end);

      return matchesEmployee && matchesTask && matchesDate;
    });

    this.totalPages = Math.ceil(filtered.length / this.itemsPerPage);
    this.filteredLogs = filtered.slice(
      (this.currentPage - 1) * this.itemsPerPage,
      this.currentPage * this.itemsPerPage
    );
  }

  clearFilters(): void {
    this.selectedEmpId = null;
    this.taskSearch = '';
    this.startDate = '';
    this.endDate = '';
    this.currentPage = 1;
    this.applyFilters();
  }

  exportToExcel(): void {
    if (!this.startDate || !this.endDate) {
      alert('Please select a valid date range to export logs.');
      return;
    }

    // Get full filtered logs (not paginated)
    const exportLogs = this.logs.filter(log => {
      const matchesEmployee = !this.selectedEmpId || log.empId === this.selectedEmpId;
      const taskName = this.getTaskName(log.taskId).toLowerCase();
      const matchesTask = !this.taskSearch || taskName.includes(this.taskSearch.toLowerCase());

      const logDate = new Date(log.date);
      const start = new Date(this.startDate);
      const end = new Date(this.endDate);
      const matchesDate = logDate >= start && logDate <= end;

      return matchesEmployee && matchesTask && matchesDate;
    });

    if (exportLogs.length === 0) {
      alert('No logs found for the selected filters.');
      return;
    }

    const worksheetData = exportLogs.map(log => {
      const task = this.tasks.find(t => t.TaskId === log.taskId);

      return {
        'Task Name': task?.Name || 'Unknown Task',
        'Employee': this.getEmployeeName(log.empId),
        'Date': log.date,
        'Time Spent': this.formatTime(log.hoursSpent, log.minutesSpent),
        'Description': log.description,
        'Expected Time (hrs)': task?.ExptedHours ?? '-'
      };
    });

    const worksheet: XLSX.WorkSheet = XLSX.utils.json_to_sheet(worksheetData);
    const workbook: XLSX.WorkBook = { Sheets: { Report: worksheet }, SheetNames: ['Report'] };
    const excelBuffer: any = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    this.saveAsExcelFile(excelBuffer, 'Task_TimeLog_Report');
  }

  private saveAsExcelFile(buffer: any, fileName: string): void {
    const EXCEL_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
    const EXCEL_EXTENSION = '.xlsx';
    const data: Blob = new Blob([buffer], { type: EXCEL_TYPE });
    FileSaver.saveAs(data, fileName + EXCEL_EXTENSION);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.applyFilters();
    }
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.applyFilters();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.applyFilters();
    }
  }
}
