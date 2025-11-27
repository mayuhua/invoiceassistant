import sys
import os

print("="*50)
print("DIAGNOSTIC TOOL")
print("="*50)
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")
print("-" * 20)

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"✅ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAILED to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR importing {module_name}: {e}")
        return False

modules = [
    "fastapi",
    "uvicorn",
    "multipart", # python-multipart usually imports as multipart or is used by fastapi
    "pdfplumber",
    "pandas",
    "openpyxl"
]

all_good = True
for mod in modules:
    if not check_import(mod):
        all_good = False

print("-" * 20)
if all_good:
    print("🎉 All dependencies appear to be installed.")
    print("Attempting to start server for 5 seconds...")
    try:
        from server import app
        print("✅ server.py imported successfully")
    except Exception as e:
        print(f"❌ FAILED to import server.py: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  Some dependencies are missing.")
    print("Try running: pip install -r requirements.txt")

print("="*50)
