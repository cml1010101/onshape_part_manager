// Data types matching the backend datatypes.py
export interface Part {
  _id?: string;
  name: string;
  description: string;
  drawing?: string | null;
  material?: string | null;
  stl_file?: string | null;
  icon_file?: string | null;
}

export interface Assembly {
  _id?: string;
  name: string;
  description: string;
  drawing?: string | null;
  icon_file?: string | null;
}

export interface Subsystem {
  _id?: string;
  name: string;
  subsystem_number: number;
  parts: Part[];
  assemblies: Assembly[];
}

export interface Project {
  _id?: string;
  year: number;
  identifier: string; // "172" or "nfr"
  project_code?: string | null; // For 172 projects: "24A", "25B", "25C", etc. For NFR: null
  name: string;
  description: string;
  subsystems: Subsystem[];
}

export interface DatabaseSummary {
  total_parts: number;
  total_assemblies: number;
  total_subsystems: number;
  total_projects: number;
  projects: Project[];
}