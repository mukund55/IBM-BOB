import zipfile
import os
from pathlib import Path

def create_dq_package():
    """Create a comprehensive ZIP package for DQ Web App"""
    
    # Define source and destination
    source_dir = Path('DQ_Analysis_code/dq_web_app')
    zip_path = Path('DQ_WebApp_Package.zip')
    
    # Files and folders to exclude
    exclude_patterns = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.db',  # Exclude database files (will be created on first run)
        '*.db-journal',
        'venv',
        '.env',
        '.git',
        '.vscode',
        'uploads/*',  # Exclude uploaded files
        'dq_output/*',  # Exclude output files
        '*.log',
        '.DS_Store',
        'Thumbs.db'
    ]
    
    def should_exclude(file_path):
        """Check if file should be excluded"""
        path_str = str(file_path)
        for pattern in exclude_patterns:
            if pattern.startswith('*'):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('/*'):
                if pattern[:-2] in path_str:
                    return True
            elif pattern in path_str:
                return True
        return False
    
    print("Creating DQ Web App Package...")
    print(f"Source: {source_dir}")
    print(f"Destination: {zip_path}")
    print()
    
    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        file_count = 0
        
        # Add all files from dq_web_app
        for root, dirs, files in os.walk(source_dir):
            # Remove excluded directories from dirs list
            dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                if should_exclude(file_path):
                    print(f"Skipping: {file_path}")
                    continue
                
                # Calculate archive name (relative path)
                arcname = file_path.relative_to(source_dir.parent)
                
                try:
                    zipf.write(file_path, arcname)
                    file_count += 1
                    if file_count % 10 == 0:
                        print(f"Added {file_count} files...")
                except Exception as e:
                    print(f"Error adding {file_path}: {e}")
        
        # Create empty directories that are needed
        empty_dirs = [
            'dq_web_app/uploads',
            'dq_web_app/dq_output',
            'dq_web_app/database'
        ]
        
        for dir_path in empty_dirs:
            zipf.writestr(f"{dir_path}/.gitkeep", "")
            print(f"Created empty directory: {dir_path}")
    
    print()
    print(f"✅ Package created successfully!")
    print(f"📦 File: {zip_path.absolute()}")
    print(f"📊 Total files: {file_count}")
    print(f"💾 Size: {zip_path.stat().st_size / (1024*1024):.2f} MB")
    print()
    print("Package contents:")
    print("- Complete dq_web_app application")
    print("- SETUP_GUIDE.md")
    print("- start_app.bat (Windows launcher)")
    print("- start_app.sh (macOS/Linux launcher)")
    print("- All templates and static files")
    print("- requirements.txt")
    print()
    print("⚠️  Note: Database and uploaded files excluded (will be created on first run)")

if __name__ == '__main__':
    create_dq_package()

# Made with Bob
