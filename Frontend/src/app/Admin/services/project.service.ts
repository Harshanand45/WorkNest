import { Injectable } from "@angular/core";

@Injectable({
  providedIn: 'root',
})
export class ProjectService {
  private projects = [
    {
      id: 1,
      projectName: 'Employee Portal',
      projectManager: 'Alice Johnson',
      startDate: '2025-05-01',
      endDate: '2025-07-15',
      status: ['In Progress'],
      priority: 'High',
       assignedEmployees : [
  {
    name: 'John Doe',
    joinDate: '2024-11-01',
    role: 'Frontend Developer',
  }],
      description:'loremeifhifehlfwhigrrhilgrohgrwjl;fehgoiwfslfjhowgjekjlhivsvrjkrufgfufrgkrfugfufugfufgfjbfjfbj'
    },
    {
      id: 2,
      projectName: 'Inventory System',
      projectManager: 'Bob Smith',
      startDate: '2025-04-10',
      endDate: '2025-06-20',
      status: ['Pending'],
      priority: 'Medium',
       assignedEmployees : [
  {
    name: 'John Doe',
    joinDate: '2024-11-01',
    role: 'Frontend Developer',
  }],
       description:'loremeifhifehlfwhigrrhilgrohgrwjl;fehgoiwfslfjhowgjekjlhivsvrjkrufgfufrgkrfugfufugfufgfjbfjfbj'
    },
    {
      id: 3,
      projectName: 'CRM Dashboard',
      projectManager: 'Carol White',
      startDate: '2025-03-05',
      endDate: '2025-05-30',
      status: ['Completed'],
      priority: 'Low',
      assignedEmployees : [
  {
    name: 'John Doe',
    joinDate: '2024-11-01',
    role: 'Frontend Developer',
  }
],

       description:'loremeifhifehlfwhigrrhilgrohgrwjl;fehgoiwfslfjhowgjekjlhivsvrjkrufgfufrgkrfugfufugfufgfjbfjfbj'
    },
  ];

  private currentId = 4;

  constructor() {}

  getProjects() {
    return this.projects;
  }

  getProjectById(id: number) {
    return this.projects.find((p) => p.id === id);
  }

  addProject(project: any) {
    project.id = this.currentId++;
    this.projects.push(project);
  }

  updateProject(updatedProject: any) {
    const index = this.projects.findIndex((p) => p.id === updatedProject.id);
    if (index > -1) this.projects[index] = updatedProject;
  }

  deleteProject(id: number) {
    this.projects = this.projects.filter((p) => p.id !== id);
  }

  addEmployeeToProject(projectId: number, employee: any) {
  const project = this.projects.find((p) => p.id === projectId);
  if (project) {
    project.assignedEmployees.push(employee);
  }
}
}
