#!/usr/bin/env python
"""
Virtual Pet Application Launcher

This script launches the Virtual Pet Application using Streamlit.
"""

import os
import sys
import subprocess

def main():
    """Run the Virtual Pet Application."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Add the current directory to the Python path
    sys.path.insert(0, script_dir)
    
    # Print a message to indicate which file is being run
    print("Starting Virtual Pet Application using app/main.py...")
    
    # Run the Streamlit application
    subprocess.run(["streamlit", "run", "app/main.py"])

if __name__ == "__main__":
    main() 