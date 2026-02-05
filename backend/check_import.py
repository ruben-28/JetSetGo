import sys
import os

# Ensure backend dir is in path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app.main...")
    from app.main import app
    print("Import successful!")
except Exception as e:
    print("Import failed!")
    import traceback
    traceback.print_exc()
