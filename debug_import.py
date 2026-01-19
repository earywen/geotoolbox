import sys
import os
print(f"CWD: {os.getcwd()}")
print(f"Path: {sys.path}")
try:
    from modules.autolabo_core.processors.base import BaseProcessor
    print("Import Successful!")
except Exception as e:
    print(f"Import Failed: {e}")
