from database import DatabaseManager
from datatypes import Project

import uuid

def main():
    db_manager = DatabaseManager()
    db_manager.print_summary()
    if db_manager.get_nfr_project() is None:
        print("Creating new NFR project...")
        nfr_project = Project(
            year=2023,
            identifier='nfr',
            project_code='NFR',
            name='NFR Project',
            description='The central project for all continuing CAD development.',
            subsystems=[]
        )
        db_manager.create_project(nfr_project)
    if db_manager.get_172_project_by_code('25A') is None:
        print("Creating new 172 project...")
        project_172 = Project(
            year=2023,
            identifier='172',
            project_code='25A',
            name='172 Project 25A',
            description='Project 25A for the 172 team.',
            subsystems=[]
        )
        db_manager.create_project(project_172)
    db_manager.print_summary()
    db_manager.close()

if __name__ == '__main__':
    main()