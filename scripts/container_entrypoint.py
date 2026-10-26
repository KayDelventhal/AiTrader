import os
import subprocess
import sys

subprocess.run([sys.executable, "scripts/migrate.py"], check=True)
os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"])
