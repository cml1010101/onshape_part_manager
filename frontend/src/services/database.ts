import type { Part, Assembly, Subsystem, Project, DatabaseSummary } from '../types';

// Mock data for development - this will be replaced with actual API calls later
const mockProjects: Project[] = [
  {
    _id: '1',
    year: 2025,
    identifier: '172',
    project_code: '25A',
    name: '172 Project 25A',
    description: 'Project 25A for the 172 team.',
    subsystems: [
      {
        _id: 's1',
        name: 'Drivetrain',
        subsystem_number: 1,
        parts: [
          {
            _id: 'p1',
            name: 'Drive Wheel',
            description: 'Main drive wheel for robot',
            material: 'Aluminum',
            drawing: null,
            stl_file: null,
            icon_file: null
          }
        ],
        assemblies: [
          {
            _id: 'a1',
            name: 'Gearbox Assembly',
            description: 'Main gearbox for drivetrain',
            drawing: null,
            icon_file: null
          }
        ]
      }
    ]
  },
  {
    _id: '2',
    year: 2023,
    identifier: 'nfr',
    project_code: null,
    name: 'NFR Project',
    description: 'The central project for all continuing CAD development.',
    subsystems: [
      {
        _id: 's2',
        name: 'Common Components',
        subsystem_number: 0,
        parts: [
          {
            _id: 'p2',
            name: 'Standard Bracket',
            description: 'Reusable mounting bracket',
            material: 'Steel',
            drawing: null,
            stl_file: null,
            icon_file: null
          }
        ],
        assemblies: []
      }
    ]
  }
];

// Mock API service
export class DatabaseService {
  static async getDatabaseSummary(): Promise<DatabaseSummary> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const total_parts = mockProjects.reduce((acc, proj) => 
      acc + proj.subsystems.reduce((subAcc, sub) => subAcc + sub.parts.length, 0), 0);
    const total_assemblies = mockProjects.reduce((acc, proj) => 
      acc + proj.subsystems.reduce((subAcc, sub) => subAcc + sub.assemblies.length, 0), 0);
    const total_subsystems = mockProjects.reduce((acc, proj) => acc + proj.subsystems.length, 0);
    
    return {
      total_parts,
      total_assemblies,
      total_subsystems,
      total_projects: mockProjects.length,
      projects: mockProjects
    };
  }

  static async createProject(project: Omit<Project, '_id'>): Promise<Project> {
    await new Promise(resolve => setTimeout(resolve, 500));
    const newProject = { ...project, _id: Date.now().toString() };
    mockProjects.push(newProject);
    return newProject;
  }

  static async createSubsystem(projectId: string, subsystem: Omit<Subsystem, '_id'>): Promise<Subsystem> {
    await new Promise(resolve => setTimeout(resolve, 500));
    const newSubsystem = { ...subsystem, _id: Date.now().toString() };
    const project = mockProjects.find(p => p._id === projectId);
    if (project) {
      project.subsystems.push(newSubsystem);
    }
    return newSubsystem;
  }

  static async createPart(projectId: string, subsystemId: string, part: Omit<Part, '_id'>): Promise<Part> {
    await new Promise(resolve => setTimeout(resolve, 500));
    const newPart = { ...part, _id: Date.now().toString() };
    const project = mockProjects.find(p => p._id === projectId);
    if (project) {
      const subsystem = project.subsystems.find(s => s._id === subsystemId);
      if (subsystem) {
        subsystem.parts.push(newPart);
      }
    }
    return newPart;
  }

  static async createAssembly(projectId: string, subsystemId: string, assembly: Omit<Assembly, '_id'>): Promise<Assembly> {
    await new Promise(resolve => setTimeout(resolve, 500));
    const newAssembly = { ...assembly, _id: Date.now().toString() };
    const project = mockProjects.find(p => p._id === projectId);
    if (project) {
      const subsystem = project.subsystems.find(s => s._id === subsystemId);
      if (subsystem) {
        subsystem.assemblies.push(newAssembly);
      }
    }
    return newAssembly;
  }
}