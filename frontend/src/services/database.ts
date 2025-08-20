import type { Part, Assembly, Subsystem, Project, DatabaseSummary } from '../types';

// Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// Database service that connects to the FastAPI backend
export class DatabaseService {
  static async getDatabaseSummary(): Promise<DatabaseSummary> {
    try {
      const response = await fetch(`${API_BASE_URL}/database/summary`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching database summary:', error);
      throw error;
    }
  }

  static async createProject(project: Omit<Project, '_id'>): Promise<Project> {
    try {
      const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(project),
      });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${error}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating project:', error);
      throw error;
    }
  }

  static async createSubsystem(projectId: string, subsystem: Omit<Subsystem, '_id'>): Promise<Subsystem> {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/subsystems`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subsystem),
      });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${error}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating subsystem:', error);
      throw error;
    }
  }

  static async createPart(projectId: string, subsystemId: string, part: Omit<Part, '_id'>): Promise<Part> {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/subsystems/${subsystemId}/parts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(part),
      });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${error}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating part:', error);
      throw error;
    }
  }

  static async createAssembly(projectId: string, subsystemId: string, assembly: Omit<Assembly, '_id'>): Promise<Assembly> {
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/subsystems/${subsystemId}/assemblies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(assembly),
      });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${error}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating assembly:', error);
      throw error;
    }
  }
}