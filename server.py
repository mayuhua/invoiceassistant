import os
import shutil
import uuid
import threading
import time
import traceback
from typing import List, Dict, Any
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Import existing logic
import convert_pdf_to_layout_text
import logic_based_extraction

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
    """加载字段映射配置"""
    config_file = Path("field_mapping_config.json")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
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
    "processed_files": [],  # 实时处理的文件列表
    "current_total": 0,
    "current_success": 0,
    "current_fail": 0
}

import json

def background_process(files_to_process: List[str]):
    """Background task to process files."""
    global processing_state

    try:
        # 重置状态
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

        print("🔍 开始数据提取...")
        try:
            # 创建文件处理回调函数
            def file_processed_callback(result):
                """实时处理单个文件完成后的回调"""
                try:
                    # 计算成功/失败状态
                    has_errors = (result.get('processing_errors') and
                                len(result.get('processing_errors', [])) > 0 and
                                str(result.get('processing_errors', [])) != '[]')

                    # 更新实时统计
                    processing_state["processed_files"].append(result)
                    processing_state["current_total"] += 1

                    if has_errors:
                        processing_state["current_fail"] += 1
                    else:
                        processing_state["current_success"] += 1

                    print(f"📊 实时统计: 总数={processing_state['current_total']}, "
                          f"成功={processing_state['current_success']}, "
                          f"失败={processing_state['current_fail']}")

                except Exception as callback_error:
                    print(f"⚠️ 统计更新失败: {callback_error}")

            # 调用带回调的数据提取函数
            logic_based_extraction.main(progress_callback=extraction_progress,
                                       file_processed_callback=file_processed_callback)
            print("📊 数据提取完成")
        except Exception as extraction_error:
            print(f"❌ 数据提取过程中发生错误: {extraction_error}")
            import traceback
            traceback.print_exc()
            raise Exception(f"数据提取失败: {str(extraction_error)}")
        
        processing_state["progress"] = 100
        
        # 3. Read Result
        processing_state["step"] = "Finalizing results..."

        if not os.path.exists(OUTPUT_FILE):
             raise Exception("Output file was not generated.")

        df = pd.read_excel(OUTPUT_FILE)
        print(f"📊 读取输出文件成功，列数: {len(df.columns)}, 行数: {len(df)}")
        print(f"📋 文件列名: {list(df.columns)}")

        # Check if processing_errors column exists
        if 'processing_errors' not in df.columns:
            print("⚠️ processing_errors列不存在，添加空列表")
            df['processing_errors'] = '[]'
        else:
            print(f"✅ processing_errors列存在，示例值: {df['processing_errors'].head().tolist()}")

        # 确保filename字段存在
        if 'filename' not in df.columns:
            print("⚠️ filename列不存在，检查AY列（临时存储）")
            if 'AY' in df.columns:
                print("✅ 找到AY列，重命名为filename")
                df = df.rename(columns={'AY': 'filename'})
            else:
                print("⚠️ AY列也不存在，创建空的filename列")
                df['filename'] = [f'file_{i+1}' for i in range(len(df))]

        # 检查并显示文件名信息
        print(f"📋 filename列示例: {df['filename'].head(5).tolist()}")

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

        print(f"📈 统计结果: 总文件={total_files}, 成功={successful_files}, 失败={failed_files}")
        
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
        # 如果有实时处理的文件，优先使用实时数据
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
    # 从配置文件读取模板路径
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
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("🚀 Klarna Invoice Processor Backend v2.4 (Full Progress & Layout)")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
