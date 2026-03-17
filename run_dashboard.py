#!/usr/bin/env python3
"""
Supervisor Dashboard Launcher
=============================

Simple script to start the DreamVision Supervisor Dashboard.

Usage:
    python run_dashboard.py

This will start the FastAPI server with the dashboard interface.
"""

import os
import sys
import subprocess

def main():
    """Start the Supervisor Dashboard server."""
    print("🚀 Starting Supervisor Dashboard...")

    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    # Start the server
    try:
        subprocess.run([
            sys.executable,
            "edge_server/api/server.py"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())