import time
import csv
import subprocess
import re
import os

LOG_FILE = "/data/local/tmp/rl_swap_training_data.csv"
INTERVAL = 2.0

def run_shell(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return ""

def get_foreground_app():
    dump = run_shell("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'")
    match = re.search(r'u0 ([\w\.]+)/', dump)
    if match:
        return match.group(1)
    return "unknown"

def get_battery_status():
    dump = run_shell("dumpsys battery")
    level_match = re.search(r'level: (\d+)', dump)
    current_match = re.search(r'current now: (-?\d+)', dump) 
    
    level = int(level_match.group(1)) if level_match else 0
    current = int(current_match.group(1)) if current_match else 0
    return level, current

def get_network_throughput():
    rx_total = 0
    tx_total = 0
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:]
            for line in lines:
                parts = line.split()
                if "wlan" in parts[0] or "rmnet" in parts[0]: 
                    rx_total += int(parts[1])
                    tx_total += int(parts[9])
    except:
        pass
    return rx_total, tx_total

def get_screen_state():
    dump = run_shell("dumpsys window policy")
    if "screenState=SCREEN_STATE_ON" in dump:
        return 1
    return 0

def init_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "app_package", "battery_level", "battery_current", "net_rx", "net_tx", "screen_state"])

def collect_step():
    timestamp = time.time()
    app = get_foreground_app()
    bat_level, bat_current = get_battery_status()
    net_rx, net_tx = get_network_throughput()
    screen = get_screen_state()
    
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, app, bat_level, bat_current, net_rx, net_tx, screen])

if __name__ == "__main__":
    init_csv()
    while True:
        collect_step()
        time.sleep(INTERVAL)