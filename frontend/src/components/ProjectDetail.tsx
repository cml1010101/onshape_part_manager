import React from 'react';
import type { Project } from '../types';

interface ProjectDetailProps {
  project: Project;
  onBack: () => void;
  onAddSubsystem: (projectId: string) => void;
  onAddPart: (projectId: string, subsystemId: string) => void;
  onAddAssembly: (projectId: string, subsystemId: string) => void;
}

export const ProjectDetail: React.FC<ProjectDetailProps> = ({ 
  project, 
  onBack, 
  onAddSubsystem, 
  onAddPart, 
  onAddAssembly 
}) => {
  return (
    <div className="project-detail">
      <div className="project-detail-header">
        <button onClick={onBack} className="back-button">← Back</button>
        <div>
          <h2>{project.name}</h2>
          <div className="project-metadata">
            <span className="project-type">{project.identifier.toUpperCase()}</span>
            {project.project_code && <span className="project-code">{project.project_code}</span>}
            <span className="project-year">Year: {project.year}</span>
          </div>
          <p className="project-description">{project.description}</p>
        </div>
        <button 
          onClick={() => onAddSubsystem(project._id!)} 
          className="add-button"
        >
          Add Subsystem
        </button>
      </div>

      <div className="subsystems-list">
        {project.subsystems.map((subsystem) => (
          <div key={subsystem._id} className="subsystem-item">
            <div className="subsystem-header">
              <h3>{subsystem.name}</h3>
              <span className="subsystem-number">#{subsystem.subsystem_number.toString().padStart(project.identifier === 'nfr' ? 4 : 2, '0')}</span>
            </div>
            
            <div className="subsystem-content">
              <div className="parts-section">
                <div className="section-header">
                  <h4>Parts ({subsystem.parts.length})</h4>
                  <button 
                    onClick={() => onAddPart(project._id!, subsystem._id!)}
                    className="add-button-small"
                  >
                    Add Part
                  </button>
                </div>
                <div className="items-grid">
                  {subsystem.parts.map((part) => (
                    <div key={part._id} className="item-card">
                      <h5>{part.name}</h5>
                      <p>{part.description}</p>
                      {part.material && <span className="material">Material: {part.material}</span>}
                    </div>
                  ))}
                </div>
              </div>

              <div className="assemblies-section">
                <div className="section-header">
                  <h4>Assemblies ({subsystem.assemblies.length})</h4>
                  <button 
                    onClick={() => onAddAssembly(project._id!, subsystem._id!)}
                    className="add-button-small"
                  >
                    Add Assembly
                  </button>
                </div>
                <div className="items-grid">
                  {subsystem.assemblies.map((assembly) => (
                    <div key={assembly._id} className="item-card">
                      <h5>{assembly.name}</h5>
                      <p>{assembly.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};