import subprocess
import time
import os
from datetime import datetime

FLAG_FILE = "flags/minifig_api_limit_date.txt"

def api_limit_hit_today():
    """Check if the API limit has already been hit today."""
    if not os.path.exists(FLAG_FILE):
        return False
    with open(FLAG_FILE, "r") as f:
        last_hit = f.read().strip()
    return last_hit == datetime.now().strftime("%Y-%m-%d")

def run_main_script():
    """Run the main arbitrage script once."""
    result = subprocess.run(["python3", "prod_scripts/run_minifigures.py"])
    return result.returncode == 0

if __name__ == "__main__":
    while not api_limit_hit_today():
        print("Running arbitrage script...")
        success = run_main_script()
        if not success:
            print("Error occurred while running the script. Exiting.")
            break
        print("Sleeping before next batch (5 sec)...")
        time.sleep(5)

    if api_limit_hit_today():
        print("API limit hit for today or script finished. Exiting.")
