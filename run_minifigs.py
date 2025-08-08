import subprocess
import time
import os
import sys
from datetime import datetime

FLAG_FILE = "flags/api_call_count.txt"
API_LIMIT = 5000

def api_limit_hit_today():
    """Check if the API limit has already been hit today or will be exceeded by next batch."""
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(FLAG_FILE):
        return False
    try:
        with open(FLAG_FILE, "r") as f:
            lines = f.readlines()
        file_date = lines[0].strip() if len(lines) > 0 else ""
        file_count = int(lines[1].strip()) if len(lines) > 1 and lines[1].strip().isdigit() else 0
    except Exception:
        file_date = ""
        file_count = 0

    # If today's date and count + estimated calls exceeds API_LIMIT, treat as limit hit
    if file_date == today:
        # Check if parts flag is in sys.argv (parts workflow)
        if "-parts" in sys.argv:
            parts_calls_per_run = 2000  # Conservative estimate for parts workflow (variable calls)
            if file_count + parts_calls_per_run > API_LIMIT:
                return True
        else:
            minifig_calls_per_run = 800  # Original estimate for regular minifigs
            if file_count + minifig_calls_per_run > API_LIMIT:
                return True
    return False

def run_main_script(sw_flag, sh_flag, parts_flag):
    """Run the main arbitrage script once, optionally with -sw or -sh."""
    if parts_flag:
        cmd = ["python3", "prod_scripts/minifig_parts_batch.py"]
    else:       
        cmd = ["python3", "prod_scripts/minifig_batch.py"]
    if sw_flag:
        cmd.append("-sw")
    elif sh_flag:
        cmd.append("-sh")
    result = subprocess.run(cmd)
    return result.returncode == 0

if __name__ == "__main__":
    sw_flag = "-sw" in sys.argv
    sh_flag = "-sh" in sys.argv
    parts_flag = "-parts" in sys.argv
    if sw_flag:
        print("Only doing starwars minifigs")
    elif sh_flag:
        print("Only doing super hero minifigs")
    if parts_flag:
        print("Considering parts")
    while not api_limit_hit_today():
        print("Running arbitrage script...")
        success = run_main_script(sw_flag, sh_flag, parts_flag)
        if not success:
            print("Error occurred while running the script. Exiting.")
            break
        print("Sleeping before next batch (5 sec)...")
        time.sleep(5)

    if api_limit_hit_today():
        print("API limit hit for today. Exiting.")
