import React, { useState } from 'react';
import type { Project, Subsystem, Part, Assembly } from '../types';

interface CreateProjectFormProps {
  onSubmit: (project: Omit<Project, '_id'>) => void;
  onCancel: () => void;
}

export const CreateProjectForm: React.FC<CreateProjectFormProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    identifier: '172' as '172' | 'nfr',
    project_code: '',
    year: new Date().getFullYear()
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      project_code: formData.identifier === 'nfr' ? null : formData.project_code,
      subsystems: []
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Create New Project</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Type:</label>
            <select
              value={formData.identifier}
              onChange={(e) => setFormData({ ...formData, identifier: e.target.value as '172' | 'nfr' })}
            >
              <option value="172">172 Project</option>
              <option value="nfr">NFR Project</option>
            </select>
          </div>
          
          {formData.identifier === '172' && (
            <div className="form-group">
              <label>Project Code (e.g., 25A, 25B):</label>
              <input
                type="text"
                value={formData.project_code}
                onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
                required
              />
            </div>
          )}
          
          <div className="form-group">
            <label>Year:</label>
            <input
              type="number"
              value={formData.year}
              onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
              required
            />
          </div>
          
          <div className="form-buttons">
            <button type="button" onClick={onCancel}>Cancel</button>
            <button type="submit">Create Project</button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface CreateSubsystemFormProps {
  onSubmit: (subsystem: Omit<Subsystem, '_id'>) => void;
  onCancel: () => void;
  projectIdentifier: string;
}

export const CreateSubsystemForm: React.FC<CreateSubsystemFormProps> = ({ onSubmit, onCancel, projectIdentifier }) => {
  const [formData, setFormData] = useState({
    name: '',
    subsystem_number: projectIdentifier === 'nfr' ? 1 : 1
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      parts: [],
      assemblies: []
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Create New Subsystem</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Subsystem Number:</label>
            <input
              type="number"
              value={formData.subsystem_number}
              onChange={(e) => setFormData({ ...formData, subsystem_number: parseInt(e.target.value) })}
              min={projectIdentifier === 'nfr' ? 0 : 0}
              max={projectIdentifier === 'nfr' ? 9999 : 99}
              required
            />
          </div>
          
          <div className="form-buttons">
            <button type="button" onClick={onCancel}>Cancel</button>
            <button type="submit">Create Subsystem</button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface CreatePartFormProps {
  onSubmit: (part: Omit<Part, '_id'>) => void;
  onCancel: () => void;
}

export const CreatePartForm: React.FC<CreatePartFormProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    material: '',
    drawing: '',
    stl_file: '',
    icon_file: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      material: formData.material || null,
      drawing: formData.drawing || null,
      stl_file: formData.stl_file || null,
      icon_file: formData.icon_file || null
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Create New Part</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Material:</label>
            <input
              type="text"
              value={formData.material}
              onChange={(e) => setFormData({ ...formData, material: e.target.value })}
            />
          </div>
          
          <div className="form-group">
            <label>Drawing File:</label>
            <input
              type="text"
              value={formData.drawing}
              onChange={(e) => setFormData({ ...formData, drawing: e.target.value })}
            />
          </div>
          
          <div className="form-group">
            <label>STL File:</label>
            <input
              type="text"
              value={formData.stl_file}
              onChange={(e) => setFormData({ ...formData, stl_file: e.target.value })}
            />
          </div>
          
          <div className="form-group">
            <label>Icon File:</label>
            <input
              type="text"
              value={formData.icon_file}
              onChange={(e) => setFormData({ ...formData, icon_file: e.target.value })}
            />
          </div>
          
          <div className="form-buttons">
            <button type="button" onClick={onCancel}>Cancel</button>
            <button type="submit">Create Part</button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface CreateAssemblyFormProps {
  onSubmit: (assembly: Omit<Assembly, '_id'>) => void;
  onCancel: () => void;
}

export const CreateAssemblyForm: React.FC<CreateAssemblyFormProps> = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    drawing: '',
    icon_file: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      drawing: formData.drawing || null,
      icon_file: formData.icon_file || null
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h3>Create New Assembly</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Drawing File:</label>
            <input
              type="text"
              value={formData.drawing}
              onChange={(e) => setFormData({ ...formData, drawing: e.target.value })}
            />
          </div>
          
          <div className="form-group">
            <label>Icon File:</label>
            <input
              type="text"
              value={formData.icon_file}
              onChange={(e) => setFormData({ ...formData, icon_file: e.target.value })}
            />
          </div>
          
          <div className="form-buttons">
            <button type="button" onClick={onCancel}>Cancel</button>
            <button type="submit">Create Assembly</button>
          </div>
        </form>
      </div>
    </div>
  );
};