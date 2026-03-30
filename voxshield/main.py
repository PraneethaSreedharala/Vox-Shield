#!/usr/bin/env python3
"""
VoxShield Unified Launcher
Runs both frontend (Streamlit) and backend (audio processing) together
"""
import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def main():
    print("🔊 Starting VoxShield...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Start backend process
    backend_script = project_root / "backend" / "main.py"
    backend_cmd = [sys.executable, str(backend_script)]
    
    print(f"Starting backend: {' '.join(backend_cmd)}")
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Give backend a moment to start
    time.sleep(2)
    
    # Start frontend process
    frontend_script = project_root / "frontend" / "app.py"
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", str(frontend_script)]
    
    print(f"Starting frontend: {' '.join(frontend_cmd)}")
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    processes = [backend_process, frontend_process]
    
    def cleanup(signum=None, frame=None):
        print("\n🛑 Shutting down VoxShield...")
        for process in processes:
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ VoxShield stopped.")
        sys.exit(0)
    
    # Register cleanup handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print("✅ VoxShield is running!")
    print("🌐 Frontend: Opening in your browser...")
    print("🎤 Backend: Audio protection is active")
    print("Press Ctrl+C to stop both components")
    
    try:
        # Monitor processes and print output
        while True:
            # Check if any process has terminated
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    name = "Backend" if i == 0 else "Frontend"
                    print(f"⚠️  {name} process terminated with code {process.returncode}")
                    cleanup()
                    return
            
            # Print any available output
            for i, process in enumerate(processes):
                try:
                    line = process.stdout.readline()
                    if line:
                        name = "BACKEND" if i == 0 else "FRONTEND"
                        print(f"[{name}] {line.strip()}")
                except:
                    pass
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
