#!/usr/bin/env python3
"""
启动原始后端服务器 - 使用您的原始模块
"""

import os
import sys
import time
import socket
import webbrowser
import threading
from pathlib import Path
from typing import List

# FastAPI imports
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

# PDF processing imports
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# 原始模块检查
try:
    import convert_pdf_to_layout_text
    import logic_based_extraction
    ORIGINAL_MODULES_AVAILABLE = True
    print("[OK] Original modules available")
except ImportError as e:
    print(f"[WARNING] Original modules not available: {e}")
    ORIGINAL_MODULES_AVAILABLE = False

class PortManager:
    """简单的端口管理器"""

    def __init__(self):
        self.used_ports = set()

    def is_port_available(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except:
            return False

    def find_available_port(self, start_port: int = 8000, max_attempts: int = 50) -> int:
        for i in range(max_attempts):
            port = start_port + i
            if self.is_port_available(port) and port not in self.used_ports:
                self.used_ports.add(port)
                return port
        return start_port

class InvoiceProcessor:
    """发票处理器"""

    def __init__(self):
        self.upload_dir = Path("uploads")
        self.output_dir = Path("output")
        self.templates_dir = Path("template")

        for directory in [self.upload_dir, self.output_dir, self.templates_dir]:
            directory.mkdir(exist_ok=True)

    def process_with_original_modules(self, pdf_files: list) -> list:
        """使用原始模块处理"""
        try:
            print(f"[INFO] Processing {len(pdf_files)} PDFs with original modules")

            # 设置临时目录
            temp_upload = Path("temp_uploads")
            temp_debug = Path("temp_debug")

            temp_upload.mkdir(exist_ok=True)
            temp_debug.mkdir(exist_ok=True)

            # 复制PDF文件到临时目录
            import shutil
            temp_pdf_files = []
            for pdf_path in pdf_files:
                temp_file = temp_upload / Path(pdf_path).name
                shutil.copy2(pdf_path, temp_file)
                temp_pdf_files.append(str(temp_file))

            # 1. PDF转换
            print(f"[INFO] Converting PDFs to text...")
            success = convert_pdf_to_layout_text.process_pdf_folder(
                str(temp_upload),
                str(temp_debug)
            )

            if not success:
                raise Exception("PDF conversion failed")

            print(f"[INFO] PDF conversion completed")

            # 2. 数据提取 - 调用main函数处理所有转换后的文本文件
            print(f"[INFO] Starting data extraction...")

            # 捕获logic_based_extraction的输出结果
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            try:
                logic_based_extraction.main()
                output_text = captured_output.getvalue()
                print(f"[INFO] Data extraction completed")
                print(f"[DEBUG] Extraction output: {output_text[:500]}...")
            finally:
                sys.stdout = old_stdout

            # 3. 读取生成的结果文件
            results = []
            output_file = Path("FORMAL_ALL_OU_COMPANIES.xlsx")
            if output_file.exists():
                import pandas as pd
                df = pd.read_excel(output_file)
                for _, row in df.iterrows():
                    result = {
                        "file_name": row.get('filename', ''),
                        "invoice_number": row.get('invoice_number', ''),
                        "invoice_date": row.get('invoice_date', ''),
                        "total_amount": row.get('total_amount', 0),
                        "currency": row.get('currency', ''),
                        "vendor_name": row.get('vendor_name', ''),
                        "processing_errors": row.get('processing_errors', '[]')
                    }
                    results.append(result)
            else:
                # 如果没有生成结果文件，创建基础结果
                for pdf_path in pdf_files:
                    result = {
                        "file_name": Path(pdf_path).name,
                        "invoice_number": "",
                        "invoice_date": "",
                        "total_amount": 0,
                        "currency": "",
                        "vendor_name": "",
                        "processing_errors": ["No results generated"]
                    }
                    results.append(result)

            # 清理临时文件
            try:
                shutil.rmtree(temp_upload)
                shutil.rmtree(temp_debug)
            except:
                pass

            return results

        except Exception as e:
            print(f"[ERROR] Original module processing failed: {e}")
            import traceback
            traceback.print_exc()

            # 返回fallback结果
            results = []
            for pdf_path in pdf_files:
                result = self.create_fallback_result(pdf_path, [f"Processing failed: {str(e)}"])
                results.append(result)
            return results

    def create_fallback_result(self, pdf_path: str, errors: list = None) -> dict:
        """创建备用结果"""
        file_name = Path(pdf_path).name
        return {
            "file_name": file_name,
            "raw_text": f"Fallback processing for {file_name}",
            "invoice_number": f"INV-{file_name[:8]}",
            "invoice_date": "2024-01-01",
            "amount": "0.00",
            "currency": "EUR",
            "vendor_name": "Fallback Vendor",
            "confidence": 0.5,
            "processing_errors": errors or ["Original modules not available"]
        }

    def save_to_excel(self, data: list) -> str:
        """保存到Excel"""
        try:
            timestamp = int(time.time())
            output_file = self.output_dir / f"invoice_results_{timestamp}.xlsx"

            if OPENPYXL_AVAILABLE and PANDAS_AVAILABLE:
                df_data = []
                for item in data:
                    df_data.append({
                        "File Name": item.get('file_name', ''),
                        "Invoice Number": item.get('invoice_number', ''),
                        "Invoice Date": item.get('invoice_date', ''),
                        "Amount": item.get('amount', ''),
                        "Currency": item.get('currency', ''),
                        "Vendor Name": item.get('vendor_name', ''),
                        "Confidence": item.get('confidence', 0),
                        "Processing Errors": '; '.join(item.get('processing_errors', []))
                    })

                df = pd.DataFrame(df_data)
                df.to_excel(output_file, index=False, engine='openpyxl')
                print(f"[OK] Saved results to: {output_file}")
            else:
                # CSV fallback
                output_file = self.output_dir / f"invoice_results_{timestamp}.csv"
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    f.write("File Name,Invoice Number,Invoice Date,Amount,Currency,Vendor Name,Confidence,Processing Errors\n")
                    for item in data:
                        errors = item.get('processing_errors', [])
                        errors_str = '; '.join(str(e) for e in errors) if errors else ''
                        f.write(f"{item.get('file_name', '')},{item.get('invoice_number', '')},{item.get('invoice_date', '')},{item.get('amount', '')},{item.get('currency', '')},{item.get('vendor_name', '')},{item.get('confidence', 0)},{errors_str}\n")
                print(f"[OK] Saved results to: {output_file}")

            return str(output_file)

        except Exception as e:
            print(f"[ERROR] Failed to save results: {e}")
            raise Exception(f"Failed to save results: {str(e)}")

    def create_template(self) -> str:
        """创建Excel模板"""
        try:
            template_file = self.templates_dir / "invoice_template.xlsx"

            if OPENPYXL_AVAILABLE:
                wb = Workbook()
                ws = wb.active
                ws.title = "Invoice Data"

                headers = [
                    "File Name",
                    "Invoice Number",
                    "Invoice Date",
                    "Amount",
                    "Currency",
                    "Vendor Name",
                    "Due Date",
                    "Status",
                    "Notes"
                ]

                for col, header in enumerate(headers, 1):
                    ws.cell(row=1, column=col, value=header)

                wb.save(template_file)
                print(f"[OK] Created Excel template: {template_file}")
            else:
                # CSV fallback
                template_file = self.templates_dir / "invoice_template.csv"
                with open(template_file, 'w', newline='', encoding='utf-8') as f:
                    f.write("File Name,Invoice Number,Invoice Date,Amount,Currency,Vendor Name,Due Date,Status,Notes\n")
                print(f"[OK] Created CSV template: {template_file}")

            return str(template_file)

        except Exception as e:
            print(f"[ERROR] Failed to create template: {e}")
            raise Exception(f"Failed to create template: {str(e)}")

class InvoiceAPI:
    """发票API服务"""

    def __init__(self, port: int):
        self.port = port
        self.app = FastAPI(title="Invoice Assistant Backend", version="1.0")
        self.processor = InvoiceProcessor()
        self.processing_state = {
            "status": "idle",
            "progress": 0,
            "step": "",
            "error": None,
            "result": None,
            "summary": None
        }
        self.setup_cors()
        self.setup_routes()

    def setup_cors(self):
        """设置CORS"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """设置API路由"""

        @self.app.get("/")
        async def root():
            return {
                "message": "Invoice Assistant Backend",
                "port": self.port,
                "original_modules": ORIGINAL_MODULES_AVAILABLE,
                "status": "running"
            }

        @self.app.post("/api/process")
        async def process_invoices(files: List[UploadFile] = File(...)):
            """处理发票上传"""
            try:
                print(f"[API] Received {len(files)} files for processing")

                # 重置状态
                self.processing_state["status"] = "processing"
                self.processing_state["progress"] = 10
                self.processing_state["step"] = "Starting file upload..."
                self.processing_state["error"] = None
                self.processing_state["result"] = None
                self.processing_state["summary"] = None

                # 清理上传目录
                for f in self.processor.upload_dir.glob("*"):
                    try:
                        f.unlink()
                    except:
                        pass

                # 保存上传的文件
                saved_files = []
                for file in files:
                    file_path = self.processor.upload_dir / file.filename
                    content = await file.read()
                    with open(file_path, "wb") as buffer:
                        buffer.write(content)
                    saved_files.append(str(file_path))

                def progress_callback(current, total):
                    if total > 0:
                        percentage = int((current / total) * 70) + 20
                        self.processing_state["progress"] = percentage
                        self.processing_state["step"] = f"Processing PDF {current}/{total}"

                # 处理文件
                self.processing_state["step"] = "Processing PDF files..."
                results = []

                if ORIGINAL_MODULES_AVAILABLE and saved_files:
                    # 使用原始模块批量处理
                    self.processing_state["progress"] = 30
                    self.processing_state["step"] = "Converting PDFs to text..."
                    results = self.processor.process_with_original_modules(saved_files)
                else:
                    # 创建fallback结果
                    for file_path in saved_files:
                        result = self.processor.create_fallback_result(file_path)
                        results.append(result)

                # 保存结果
                self.processing_state["step"] = "Saving results..."
                self.processing_state["progress"] = 90
                output_file = self.processor.save_to_excel(results)

                # 完成处理
                self.processing_state["progress"] = 100
                self.processing_state["step"] = "Completed"
                self.processing_state["status"] = "completed"
                self.processing_state["result"] = results
                self.processing_state["summary"] = {
                    "totalFiles": len(results),
                    "successfulFiles": sum(1 for r in results if not r.get('processing_errors')),
                    "failedFiles": sum(1 for r in results if r.get('processing_errors'))
                }

                print(f"[SUCCESS] Processing completed: {len(results)} files")
                return {"message": "Processing completed", "status": "completed"}

            except Exception as e:
                print(f"[ERROR] Processing error: {e}")
                self.processing_state["status"] = "error"
                self.processing_state["error"] = str(e)
                self.processing_state["step"] = "Failed"
                import traceback
                traceback.print_exc()

                return {"error": f"Processing failed: {str(e)}"}, 500

        @self.app.get("/api/status")
        async def get_status():
            if self.processing_state["status"] == "completed":
                summary = self.processing_state["summary"]
                if summary:
                    return JSONResponse(
                        content={
                            "status": "completed",
                            "summary": {
                                "totalFiles": summary["totalFiles"],
                                "successfulFiles": summary["successfulFiles"],
                                "failedFiles": summary["failedFiles"],
                                "totalAmount": 0
                            }
                        }
                    )

            return JSONResponse(content={
                "status": self.processing_state.get("status", "idle"),
                "progress": self.processing_state.get("progress", 0),
                "current_step": self.processing_state.get("step", ""),
                "error": self.processing_state.get("error"),
                "processed_files": []
            })

        @self.app.get("/api/results")
        async def get_results():
            if self.processing_state["status"] == "completed" and self.processing_state["result"]:
                return JSONResponse(content={
                    "success": True,
                    "message": "Results retrieved successfully",
                    "data": self.processing_state["result"]
                })
            else:
                return JSONResponse(content={
                    "success": False,
                    "message": "No results available"
                }, status_code=404)

        @self.app.get("/api/download")
        async def download_results():
            try:
                output_files = list(self.processor.output_dir.glob("*.xlsx")) + \
                              list(self.processor.output_dir.glob("*.csv"))

                if output_files:
                    latest_file = max(output_files, key=lambda f: f.stat().st_mtime)
                    return FileResponse(
                        path=str(latest_file),
                        filename=latest_file.name,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    raise HTTPException(status_code=404, detail="No results file found")

            except Exception as e:
                print(f"[ERROR] Download error: {e}")
                raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

        @self.app.get("/api/template")
        async def download_template():
            try:
                template_file = self.processor.create_template()
                return FileResponse(
                    path=template_file,
                    name="invoice_template.xlsx",
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                print(f"[ERROR] Template error: {e}")
                raise HTTPException(status_code=500, detail=f"Template creation failed: {str(e)}")

    def run(self):
        """运行API服务器"""
        try:
            print(f"[API] Starting backend server on port {self.port}")
            print(f"[API] Original modules: {ORIGINAL_MODULES_AVAILABLE}")
            print(f"[API] PDF processing: {PDF_AVAILABLE}")
            print(f"[API] Excel export: {OPENPYXL_AVAILABLE}")

            uvicorn.run(
                self.app,
                host="127.0.0.1",
                port=self.port,
                log_level="error"
            )

        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    print("="*60)
    print("        Original Invoice Assistant Backend")
    print("        Using your original PDF processing modules")
    print("="*60)

    port_manager = PortManager()
    port = port_manager.find_available_port(8000)

    api = InvoiceAPI(port)
    api.run()

if __name__ == "__main__":
    main()