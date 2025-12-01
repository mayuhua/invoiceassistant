# Portable version deployment script
# create_portable_version.py

import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_portable_version():
    """Create portable version of Invoice Assistant"""
    
    # Create portable version directory
    import time
    timestamp = int(time.time())
    portable_dir = Path(f"invoice_assistant_portable_{timestamp}")
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir()
    
    print("Creating portable version...")
    
    # 1. Copy Python environment
    print("Copying Python environment...")
    python_exe = sys.executable
    python_dir = Path(python_exe).parent
    shutil.copytree(python_dir, portable_dir / "python", dirs_exist_ok=True)
    
    # 2. Copy project files
    print("Copying project files...")
    project_files = [
        "server.py",
        "start_backend.py", 
        "requirements.txt",
        "convert_pdf_to_layout_text.py",
        "logic_based_extraction.py",
        "port_manager.py",
        "field_mapping_config.json",
        "port_config.json",
        "FORMAL_ALL_OU_COMPANIES.xlsx"
    ]
    
    for file in project_files:
        if Path(file).exists():
            shutil.copy2(file, portable_dir)
    
    # 3. Copy frontend files
    print("Copying frontend files...")
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        shutil.copytree(frontend_dist, portable_dir / "static", dirs_exist_ok=True)

        # Modify index.html to include config scripts
        index_file = portable_dir / "static" / "index.html"
        if index_file.exists():
            content = index_file.read_text(encoding='utf-8')
            # Add config scripts before main script
            modified_content = content.replace(
                '<script type="module" crossorigin src="/assets/index-aoD-RmXb.js"></script>',
                '<script src="/config.js"></script>\n    <script src="/port-config.js"></script>\n    <script type="module" crossorigin src="/assets/index-aoD-RmXb.js"></script>'
            )
            index_file.write_text(modified_content, encoding='utf-8')
            print("Modified index.html to include port configuration")
    else:
        print("WARNING: Frontend dist directory not found (frontend/dist)")
    
    # 4. Copy folders
    folders = ["Template", "uploads", "invoices", "temp_uploads", "debug_txt"]
    for folder in folders:
        if Path(folder).exists():
            shutil.copytree(folder, portable_dir / folder, dirs_exist_ok=True)
    
    # 5. Dependencies check
    print("Dependencies included in Python environment")
    
    # 6. Create startup scripts
    print("Creating startup scripts...")
    
    # Windows batch file
    with open(portable_dir / "start.bat", "w", encoding="utf-8") as f:
        f.write("""@echo off
title Invoice Assistant
echo Starting Invoice Assistant...
cd /d "%~dp0"

REM Start server in a new window but keep it open if it crashes
start "Invoice Assistant Server" cmd /k "python\\python.exe server.py"

echo Invoice Assistant started.
echo The server window will show the actual port (usually 8080-8099).
echo Please check the server window for the URL.
echo.
echo If the browser does not open automatically, please visit:
echo http://localhost:8080
echo (or check the server window for the correct port)
echo.
pause
""")
    
    # PowerShell script
    with open(portable_dir / "start.ps1", "w", encoding="utf-8") as f:
        f.write("""# PowerShell Startup Script
Write-Host "Starting Invoice Assistant..." -ForegroundColor Green
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PWD
Start-Process "python\\python.exe" -ArgumentList "server.py"
Write-Host "Invoice Assistant started. Please visit: http://localhost:8080" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
""")
    
    # 7. Create stop script
    with open(portable_dir / "stop.bat", "w", encoding="utf-8") as f:
        f.write("""@echo off
echo Stopping Invoice Assistant...
taskkill /f /im python.exe 2>nul
echo Invoice Assistant stopped.
pause
""")
    
    # 8. Create README
    with open(portable_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write("""Invoice Assistant Portable Version - User Guide

1. System Requirements:
- Windows 7/10/11
- No Python installation required

2. How to Use:
1. Double-click 'start.bat' to start the application.
2. Open your browser and visit http://localhost:8080.
3. Upload PDF files for processing.
4. Double-click 'stop.bat' to stop the application.

3. Notes:
- The first startup might take a few minutes.
- Do not delete this folder while the application is running.
- Processed files are saved in the 'invoices' folder.
- Exported results are saved in the program directory.

4. Support:
GitHub: https://github.com/mayuhua/invoiceassistant

5. Updates:
Simply replace the files to update. No re-installation needed.
""")
    
    # 9. Create version info
    import datetime
    with open(portable_dir / "version.txt", "w", encoding="utf-8") as f:
        f.write("Invoice Assistant Portable v1.0.0\n")
        f.write(f"Build Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Python Version: {sys.version}\n")
    
    print("Portable version created successfully!")
    print(f"Location: {portable_dir.absolute()}")
    print("\nHow to use:")
    print(f"   1. Go to {portable_dir} directory")
    print("   2. Double-click start.bat")
    print("   3. Check server window for the correct URL (usually http://localhost:8080)")

if __name__ == "__main__":
    create_portable_version()