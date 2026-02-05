from datetime import datetime, timedelta
import re
import subprocess



def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr
def get_chrome_version():
    command = "google-chrome --version"
    stdout, stderr = run_command(command)

    print("Standard Output:", stdout.strip().split(' ')[-1].split('.')[0])
    pass