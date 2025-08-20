import React from 'react';
import type { DatabaseSummary } from '../types';

interface DatabaseSummaryProps {
  summary: DatabaseSummary;
}

export const DatabaseSummaryComponent: React.FC<DatabaseSummaryProps> = ({ summary }) => {
  return (
    <div className="database-summary">
      <h2>Database Summary</h2>
      <div className="summary-stats">
        <div className="stat-card">
          <h3>Projects</h3>
          <span className="stat-number">{summary.total_projects}</span>
        </div>
        <div className="stat-card">
          <h3>Subsystems</h3>
          <span className="stat-number">{summary.total_subsystems}</span>
        </div>
        <div className="stat-card">
          <h3>Parts</h3>
          <span className="stat-number">{summary.total_parts}</span>
        </div>
        <div className="stat-card">
          <h3>Assemblies</h3>
          <span className="stat-number">{summary.total_assemblies}</span>
        </div>
      </div>
    </div>
  );
};