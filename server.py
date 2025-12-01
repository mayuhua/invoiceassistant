import os
import sys
import shutil
import uuid
import threading
import time
import traceback
import json
from typing import List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uvicorn

# Fix for PyInstaller - Redirect stdout/stderr to avoid NoneType issues
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    import io
    import os

    # Create safe replacements for stdout/stderr
    if sys.stdout is None or not hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(open(os.devnull, 'wb'), encoding='utf-8')

    if sys.stderr is None or not hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(open(os.devnull, 'wb'), encoding='utf-8')

# Import existing logic
import convert_pdf_to_layout_text
import logic_based_extraction
import port_manager

# Get dynamic port configuration
# Force a fresh check for a free port
try:
    port_config = port_manager.get_port_config()
    BACKEND_PORT = port_config["backend_port"]
except Exception as e:
    print(f"Error getting port config: {e}, using default 8000")
    BACKEND_PORT = 8000

app = FastAPI()

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = Path("temp_uploads")
DEBUG_TXT_DIR = Path("debug_txt")
OUTPUT_FILE = "FORMAL_ALL_OU_COMPANIES.xlsx"
TEMPLATE_FILE = Path("Template/导出模板.xlsx")

# Load field mapping config
def load_field_mapping_config():
    """Load field mapping configuration"""
    config_file = Path("field_mapping_config.json")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"[ERROR] Failed to load configuration file: {e}")
        return {
            "template_file": "Template/导出模板.xlsx",
            "start_row": 5,
            "header_row": 1,
            "sheet_name": "Sheet1"
        }

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
DEBUG_TXT_DIR.mkdir(exist_ok=True)

# Global State for Progress Tracking
# In a multi-user production app, this should be a database or Redis keyed by job_id.
# For this single-user local app, a global dict is sufficient.
processing_state: Dict[str, Any] = {
    "status": "idle",  # idle, processing, completed, error
    "step": "",        # Current step description
    "progress": 0,     # 0-100
    "error": None,
    "result": None,
    "summary": None,
    "processed_files": [],  # Real-time processed files list
    "current_total": 0,
    "current_success": 0,
    "current_fail": 0
}

import json

def background_process(files_to_process: List[str]):
    """Background task to process files."""
    global processing_state

    try:
        # Reset state
        processing_state["status"] = "processing"
        processing_state["progress"] = 10
        processing_state["error"] = None
        processing_state["result"] = None
        processing_state["summary"] = None
        processing_state["processed_files"] = []
        processing_state["current_total"] = 0
        processing_state["current_success"] = 0
        processing_state["current_fail"] = 0
        
        # 1. PDF Conversion (0-50%)
        processing_state["step"] = "Converting PDFs to text..."
        print("Starting PDF conversion...")
        
        # Clean up debug_txt before starting
        for f in DEBUG_TXT_DIR.glob("*"):
            try:
                os.remove(f)
            except Exception:
                pass

        def pdf_progress(current, total):
            # Map PDF conversion to 0-50% range
            if total > 0:
                percentage = int((current / total) * 50)
                processing_state["progress"] = percentage
                processing_state["step"] = f"Converting PDF {current}/{total}..."

        success = convert_pdf_to_layout_text.process_pdf_folder(
            str(UPLOAD_DIR), 
            str(DEBUG_TXT_DIR),
            progress_callback=pdf_progress
        )
        
        if not success:
            raise Exception("PDF conversion failed. Please check if the files are valid PDFs.")
            
        processing_state["progress"] = 50
        
        # 2. Data Extraction (50-100%)
        processing_state["step"] = "Extracting data from invoices..."
        print("Starting Data Extraction...")

        def extraction_progress(current, total):
            # Map Extraction to 50-100% range
            if total > 0:
                percentage = 50 + int((current / total) * 50)
                processing_state["progress"] = percentage
                processing_state["step"] = f"Extracting Data {current}/{total}..."

        print("[INFO] Starting data extraction...")
        try:
            # Create file processing callback function
            def file_processed_callback(result):
                """Callback for real-time processing of individual files"""
                try:
                    # Calculate success/failure status
                    has_errors = (result.get('processing_errors') and
                                len(result.get('processing_errors', [])) > 0 and
                                str(result.get('processing_errors', [])) != '[]')

                    # Update real-time statistics
                    processing_state["processed_files"].append(result)
                    processing_state["current_total"] += 1

                    if has_errors:
                        processing_state["current_fail"] += 1
                    else:
                        processing_state["current_success"] += 1

                    print(f"[STATS] Real-time stats: Total={processing_state['current_total']}, "
                          f"Success={processing_state['current_success']}, "
                          f"Failed={processing_state['current_fail']}")

                except Exception as callback_error:
                    print(f"[WARN] Statistics update failed: {callback_error}")

            # Call data extraction function with callback
            logic_based_extraction.main(progress_callback=extraction_progress,
                                       file_processed_callback=file_processed_callback)
            print("[INFO] Data extraction completed")
        except Exception as extraction_error:
            print(f"[ERROR] Error occurred during data extraction: {extraction_error}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Data extraction failed: {str(extraction_error)}")
        
        processing_state["progress"] = 100
        
        # 3. Read Result
        processing_state["step"] = "Finalizing results..."

        if not os.path.exists(OUTPUT_FILE):
             raise Exception("Output file was not generated.")

        df = pd.read_excel(OUTPUT_FILE)
        print(f"[INFO] Successfully read output file, columns: {len(df.columns)}, rows: {len(df)}")
        print(f"[INFO] File column names: {list(df.columns)}")

        # Check if processing_errors column exists
        if 'processing_errors' not in df.columns:
            print("[WARN] processing_errors column does not exist, adding empty list")
            df['processing_errors'] = '[]'
        else:
            print(f"[OK] processing_errors column exists, example values: {df['processing_errors'].head().tolist()}")

        # Ensure filename field exists
        if 'filename' not in df.columns:
            print("[WARN] filename column does not exist, creating default values")
            df['filename'] = [f'file_{i+1}' for i in range(len(df))]

        # Check and display filename information
        print(f"[INFO] filename column examples: {df['filename'].head(5).tolist()}")

        # SAFE JSON CONVERSION:
        # Pandas to_dict() can leave numpy types which crash FastAPI.
        # Using to_json() then json.loads() ensures everything is standard Python types.
        data_json_str = df.to_json(orient="records", date_format="iso")
        data = json.loads(data_json_str)

        print(f"📊 转换为JSON成功，记录数: {len(data)}")

        # Calculate summary
        # We need to be careful with numpy booleans here too
        total_files = len(df)

        def is_successful(errors):
            """Check if processing was successful based on errors field"""
            if pd.isna(errors):
                return True
            errors_str = str(errors).strip()
            return errors_str == '' or errors_str == '[]' or errors_str == 'nan'

        # Add debug info for each record
        for idx, row in df.iterrows():
            filename = row.get('filename', 'unknown')
            errors = row.get('processing_errors', '[]')
            success = is_successful(errors)
            print(f"Record {idx}: filename={filename}, errors={errors}, success={success}")

        successful_files = len(df[df['processing_errors'].apply(is_successful)])
        failed_files = len(df[df['processing_errors'].apply(lambda x: not is_successful(x))])

        print(f"📈 Statistics: Total files={total_files}, Successful={successful_files}, Failed={failed_files}")
        
        summary = {
            "totalFiles": int(total_files),
            "successfulFiles": int(successful_files),
            "failedFiles": int(failed_files),
        }
        
        processing_state["result"] = data
        processing_state["summary"] = summary
        processing_state["status"] = "completed"
        processing_state["progress"] = 100
        processing_state["step"] = "Completed"
        
    except Exception as e:
        print(f"Background process failed: {e}")
        traceback.print_exc()
        processing_state["status"] = "error"
        processing_state["error"] = str(e)
        processing_state["step"] = "Failed"

@app.post("/api/process")
async def process_invoices(files: List[UploadFile] = File(...)):
    global processing_state
    
    # Reset state if not already processing
    if processing_state["status"] == "processing":
        return JSONResponse(
            content={"error": "Already processing files. Please wait."}, 
            status_code=409
        )

    try:
        # Clean up previous uploads
        for f in UPLOAD_DIR.glob("*"):
            try:
                os.remove(f)
            except Exception:
                pass
        
        # Save uploaded files
        saved_files = []
        for file in files:
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            
        # Start background thread
        thread = threading.Thread(target=background_process, args=(saved_files,))
        thread.daemon = True
        thread.start()
        
        return {"message": "Processing started", "status": "processing"}

    except Exception as e:
        return JSONResponse(content={"error": f"Failed to start processing: {str(e)}"}, status_code=500)

@app.get("/api/status")
async def get_status():
    try:
        # If there are real-time processed files, prioritize real-time data
        if processing_state["processed_files"]:
            return JSONResponse(content={
                **processing_state,
                "result": processing_state["processed_files"],
                "summary": {
                    "totalFiles": processing_state["current_total"],
                    "successfulFiles": processing_state["current_success"],
                    "failedFiles": processing_state["current_fail"]
                }
            })
        else:
            return JSONResponse(content=processing_state)
    except Exception as e:
        print(f"Error in get_status: {e}")
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/template")
async def download_template():
    """Serve the template file as read-only"""
    # Read template path from configuration file
    config = load_field_mapping_config()
    template_path = Path(config.get('template_file', 'Template/导出文件.xlsx'))

    if template_path.exists():
        return FileResponse(
            template_path,
            filename="导出模板.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return JSONResponse(content={"error": f"Template file not found: {template_path}"}, status_code=404)

@app.get("/api/download")
async def download_result(filename: str = "extracted_invoices.xlsx"):
    if os.path.exists(OUTPUT_FILE):
        # Ensure extension is .xlsx
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        return FileResponse(OUTPUT_FILE, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return JSONResponse(content={"error": "File not found"}, status_code=404)

# Serve Frontend Static Files
FRONTEND_DIST = Path("frontend/dist")
PORTABLE_STATIC = Path("static")

# Create dynamic frontend config for portable mode
def create_frontend_config():
    """Create frontend config file with current backend port"""
    config_content = f"""// Dynamic configuration - will be updated by the backend
window.API_BASE_URL = 'http://localhost:{BACKEND_PORT}';
window.DYNAMIC_PORT_SUPPORT = true;
window.BACKEND_PORT = {BACKEND_PORT};
"""

    # Try to create config.js in both frontend locations
    config_paths = [
        Path("frontend/config.js"),
        Path("static/config.js"),
        PORTABLE_STATIC / "config.js" if PORTABLE_STATIC.exists() else None
    ]

    config_created = False
    for config_path in config_paths:
        if config_path and config_path.parent.exists():
            try:
                config_path.write_text(config_content)
                print(f"Created frontend config at: {config_path}")
                config_created = True
                break
            except Exception as e:
                print(f"Could not create config at {config_path}: {e}")
                continue

    # Also create port-config.js as backup
    if config_created:
        port_config_content = f"""// Port Configuration Injector - Backup
window.DYNAMIC_PORT_SUPPORT = true;
window.BACKEND_PORT = {BACKEND_PORT};
window.API_BASE_URL = 'http://localhost:{BACKEND_PORT}';
console.log('Port Configuration Injected: Port {BACKEND_PORT}');
"""

        port_config_paths = [
            Path("static/port-config.js"),
            PORTABLE_STATIC / "port-config.js" if PORTABLE_STATIC.exists() else None
        ]

        for port_config_path in port_config_paths:
            if port_config_path and port_config_path.parent.exists():
                try:
                    port_config_path.write_text(port_config_content)
                    print(f"Created port config at: {port_config_path}")
                    break
                except Exception as e:
                    print(f"Could not create port config at {port_config_path}: {e}")
                    continue

    # Create an additional API endpoint to serve config directly
    @app.get("/config.js")
    async def serve_config_js():
        """Serve config.js directly to avoid static file issues"""
        if not config_created:
            return JSONResponse(content={"error": "Config not created"}, status_code=500)

        return Response(
            content=config_content,
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache"}
        )

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
elif PORTABLE_STATIC.exists():
    print(f"Serving frontend from portable static directory: {PORTABLE_STATIC.absolute()}")
    app.mount("/", StaticFiles(directory=str(PORTABLE_STATIC), html=True), name="static")
else:
    print("WARNING: Frontend static files not found!")

if __name__ == "__main__":
    print("="*70)
    print("Klarna Invoice Processor Backend v2.5 (Dynamic Port Support)")
    print("="*70)
    print(f"Starting backend on dynamic port: {BACKEND_PORT}")
    print(f"API will be available at: http://localhost:{BACKEND_PORT}")
    print("="*70)

    # Create frontend configuration for portable mode
    create_frontend_config()

    # Update frontend config (only if directory exists, skip in portable mode)
    try:
        port_manager.update_frontend_config(BACKEND_PORT)
        print(f"Updated frontend config for backend port {BACKEND_PORT}")
    except Exception as e:
        print(f"Skipped frontend config update (likely in portable mode): {e}")

    # Configure uvicorn with fixed logging for PyInstaller
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=BACKEND_PORT,
            log_config=None,  # Disable custom logging config to avoid NoneType errors
            access_log=True   # Enable basic access logs
        )
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e):
            print(f"Port {BACKEND_PORT} is already in use. Please stop the other service or try a different port.")
            print("You can also run the application again - it will automatically find a free port.")
        else:
            print(f"Failed to start server: {e}")
    except Exception as e:
        print(f"Unexpected error starting server: {e}")
