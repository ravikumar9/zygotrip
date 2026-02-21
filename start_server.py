#!/usr/bin/env python
"""
Start Django development server on port 8042
"""
import os
import subprocess
import time
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')

# Change to project directory
project_dir = r'c:\Users\ravi9\Downloads\Zy\zygotrip'
os.chdir(project_dir)

# Start server
process = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8042', '--noreload'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print(f"Server process started (PID: {process.pid})")
print("Waiting for server to start...")
time.sleep(3)

if process.poll() is None:
    print("OK - Server is running on http://localhost:8042")
else:
    print("ERROR - Server failed to start")
    print(process.communicate()[0])
    sys.exit(1)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    process.terminate()