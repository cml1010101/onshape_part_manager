# Onshape Part Manager - Frontend

A React TypeScript frontend for the Onshape Part Manager, built with Vite.

## Features

- **Database Summary**: View overview of projects, subsystems, parts, and assemblies
- **Project Management**: Browse and manage 172 and NFR projects
- **Parts & Assemblies**: Create and view parts and assemblies within subsystems
- **Clean UI**: Simple, responsive design built with modern React patterns

## Getting Started

### Prerequisites
- Node.js (v16 or higher)
- npm

### Installation
```bash
cd frontend
npm install
```

### Development
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) to view the application.

### Build
```bash
npm run build
```

### Lint
```bash
npm run lint
```

## Project Structure

```
src/
├── components/          # React components
│   ├── DatabaseSummary.tsx
│   ├── ProjectList.tsx
│   ├── ProjectDetail.tsx
│   └── Forms.tsx
├── services/           # API services and mock data
│   └── database.ts
├── types/             # TypeScript type definitions
│   └── index.ts
├── App.tsx            # Main application component
├── App.css            # Application styles
└── main.tsx           # Application entry point
```

## Features Detail

### Database Summary
Displays count cards showing total projects, subsystems, parts, and assemblies in the system.

### Project List
Shows all projects with their basic information:
- Project name, type (172/NFR), and project code
- Description and summary statistics
- Click to view project details

### Project Detail View
Detailed view of a project showing:
- Project metadata (name, type, code, year, description)
- All subsystems with their parts and assemblies
- Add buttons for creating new subsystems, parts, and assemblies

### Forms
Modal forms for creating:
- **Projects**: Name, description, type (172/NFR), project code (for 172), year
- **Subsystems**: Name and subsystem number
- **Parts**: Name, description, material, and file references
- **Assemblies**: Name, description, and file references

## Data Structure

The frontend mirrors the backend data structure:
- **Project**: Container for subsystems with metadata
- **Subsystem**: Container for parts and assemblies with auto-numbering
- **Part**: Individual components with material and file information
- **Assembly**: Collections of parts with documentation

## Mock Data

Currently uses mock data for development. The `DatabaseService` class in `services/database.ts` provides:
- Sample 172 and NFR projects
- Simulated API delays
- In-memory CRUD operations

To connect to the real backend, replace the mock service calls with actual HTTP requests to the Python backend API.

## Styling

Uses CSS custom properties for consistent theming:
- Primary color: #007acc (blue)
- Clean card-based layout
- Responsive design for mobile and desktop
- Hover effects and transitions
