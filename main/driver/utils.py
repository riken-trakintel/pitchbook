from datetime import datetime, timedelta
import re
import subprocess


def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr


def get_chrome_version():
    """Get the installed Chrome version"""
    command = "google-chrome --version"
    stdout, stderr = run_command(command)
    
    if stdout:
        version = stdout.strip().split(' ')[-1].split('.')[0]
        print("Chrome Version:", version)
        return int(version)
    return 143  # Default version
