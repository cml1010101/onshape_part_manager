import { useState, useEffect } from 'react';
import './App.css';
import type { DatabaseSummary as DatabaseSummaryType, Project, Subsystem, Part, Assembly } from './types';
import { DatabaseService } from './services/database';
import { DatabaseSummaryComponent } from './components/DatabaseSummary';
import { ProjectList } from './components/ProjectList';
import { ProjectDetail } from './components/ProjectDetail';
import { 
  CreateProjectForm, 
  CreateSubsystemForm, 
  CreatePartForm, 
  CreateAssemblyForm 
} from './components/Forms';

type FormMode = 'none' | 'project' | 'subsystem' | 'part' | 'assembly';

function App() {
  const [summary, setSummary] = useState<DatabaseSummaryType | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [formMode, setFormMode] = useState<FormMode>('none');
  const [formContext, setFormContext] = useState<{ projectId?: string; subsystemId?: string }>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await DatabaseService.getDatabaseSummary();
      setSummary(data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = (project: Project) => {
    setSelectedProject(project);
  };

  const handleBackToList = () => {
    setSelectedProject(null);
  };

  const handleCreateProject = async (projectData: Omit<Project, '_id'>) => {
    try {
      await DatabaseService.createProject(projectData);
      await loadData();
      setFormMode('none');
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const handleCreateSubsystem = async (subsystemData: Omit<Subsystem, '_id'>) => {
    try {
      if (formContext.projectId) {
        await DatabaseService.createSubsystem(formContext.projectId, subsystemData);
        await loadData();
        // Update selected project if it's currently displayed
        if (selectedProject && selectedProject._id === formContext.projectId) {
          const updatedSummary = await DatabaseService.getDatabaseSummary();
          const updatedProject = updatedSummary.projects.find(p => p._id === formContext.projectId);
          if (updatedProject) {
            setSelectedProject(updatedProject);
          }
        }
      }
      setFormMode('none');
      setFormContext({});
    } catch (error) {
      console.error('Failed to create subsystem:', error);
    }
  };

  const handleCreatePart = async (partData: Omit<Part, '_id'>) => {
    try {
      if (formContext.projectId && formContext.subsystemId) {
        await DatabaseService.createPart(formContext.projectId, formContext.subsystemId, partData);
        await loadData();
        // Update selected project if it's currently displayed
        if (selectedProject && selectedProject._id === formContext.projectId) {
          const updatedSummary = await DatabaseService.getDatabaseSummary();
          const updatedProject = updatedSummary.projects.find(p => p._id === formContext.projectId);
          if (updatedProject) {
            setSelectedProject(updatedProject);
          }
        }
      }
      setFormMode('none');
      setFormContext({});
    } catch (error) {
      console.error('Failed to create part:', error);
    }
  };

  const handleCreateAssembly = async (assemblyData: Omit<Assembly, '_id'>) => {
    try {
      if (formContext.projectId && formContext.subsystemId) {
        await DatabaseService.createAssembly(formContext.projectId, formContext.subsystemId, assemblyData);
        await loadData();
        // Update selected project if it's currently displayed
        if (selectedProject && selectedProject._id === formContext.projectId) {
          const updatedSummary = await DatabaseService.getDatabaseSummary();
          const updatedProject = updatedSummary.projects.find(p => p._id === formContext.projectId);
          if (updatedProject) {
            setSelectedProject(updatedProject);
          }
        }
      }
      setFormMode('none');
      setFormContext({});
    } catch (error) {
      console.error('Failed to create assembly:', error);
    }
  };

  const openCreateSubsystemForm = (projectId: string) => {
    setFormContext({ projectId });
    setFormMode('subsystem');
  };

  const openCreatePartForm = (projectId: string, subsystemId: string) => {
    setFormContext({ projectId, subsystemId });
    setFormMode('part');
  };

  const openCreateAssemblyForm = (projectId: string, subsystemId: string) => {
    setFormContext({ projectId, subsystemId });
    setFormMode('assembly');
  };

  const closeForm = () => {
    setFormMode('none');
    setFormContext({});
  };

  if (loading) {
    return <div className="loading">Loading database...</div>;
  }

  if (!summary) {
    return <div className="error">Failed to load database</div>;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Onshape Part Manager</h1>
        {!selectedProject && (
          <button onClick={() => setFormMode('project')} className="add-button">
            Add Project
          </button>
        )}
      </header>

      <main className="app-main">
        {selectedProject ? (
          <ProjectDetail
            project={selectedProject}
            onBack={handleBackToList}
            onAddSubsystem={openCreateSubsystemForm}
            onAddPart={openCreatePartForm}
            onAddAssembly={openCreateAssemblyForm}
          />
        ) : (
          <>
            <DatabaseSummaryComponent summary={summary} />
            <ProjectList projects={summary.projects} onSelectProject={handleSelectProject} />
          </>
        )}
      </main>

      {/* Forms */}
      {formMode === 'project' && (
        <CreateProjectForm onSubmit={handleCreateProject} onCancel={closeForm} />
      )}
      {formMode === 'subsystem' && selectedProject && (
        <CreateSubsystemForm 
          onSubmit={handleCreateSubsystem} 
          onCancel={closeForm}
          projectIdentifier={selectedProject.identifier}
        />
      )}
      {formMode === 'part' && (
        <CreatePartForm onSubmit={handleCreatePart} onCancel={closeForm} />
      )}
      {formMode === 'assembly' && (
        <CreateAssemblyForm onSubmit={handleCreateAssembly} onCancel={closeForm} />
      )}
    </div>
  );
}

export default App;
