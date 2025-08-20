import React from 'react';
import type { Project } from '../types';

interface ProjectListProps {
  projects: Project[];
  onSelectProject: (project: Project) => void;
}

export const ProjectList: React.FC<ProjectListProps> = ({ projects, onSelectProject }) => {
  return (
    <div className="project-list">
      <h3>Projects</h3>
      {projects.map((project) => (
        <div key={project._id} className="project-item" onClick={() => onSelectProject(project)}>
          <div className="project-header">
            <h4>{project.name}</h4>
            <span className="project-type">{project.identifier.toUpperCase()}</span>
            {project.project_code && <span className="project-code">{project.project_code}</span>}
          </div>
          <p className="project-description">{project.description}</p>
          <div className="project-stats">
            <span>{project.subsystems.length} subsystems</span>
            <span>•</span>
            <span>
              {project.subsystems.reduce((acc, sub) => acc + sub.parts.length, 0)} parts
            </span>
            <span>•</span>
            <span>
              {project.subsystems.reduce((acc, sub) => acc + sub.assemblies.length, 0)} assemblies
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};