#!/opt/canzuki/python/3.12.4/bin/python
import os
import socket
import time
import datetime
#import psutil
import subprocess
import json
from pathlib import Path

# Directories
data = "/opt/canzuki/data"
logs = "/opt/canzuki/logs"

# Make directories
os.makedirs(data, exist_ok=True)
os.makedirs(logs, exist_ok=True)

# Cleanup function
def clean_up():
    toclean = Path(data)
    log_file = Path(logs) / f"cleanUp.{datetime.datetime.utcnow().isoweekday()}"
    
    with open(log_file, 'w') as log:
        for file in toclean.glob('*'):
            if file.is_file() and (datetime.datetime.now() - datetime.datetime.fromtimestamp(file.stat().st_mtime)).days > 1:
                log.write(f"{file}\n")
                file.unlink()

clean_up()


def get_ip_addresses():
    ip_addresses = []

    try:
        # Run 'ip' command to get network interfaces information
        result = subprocess.run(['/sbin/ip', '-4', 'addr', 'show'], capture_output=True, text=True)
        lines = result.stdout.splitlines()

        for line in lines:
            if 'inet ' in line:
                # Extract the IP address
                parts = line.split()
                ip = parts[1].split('/')[0]
                if not ip.startswith('127.'):
                    ip_addresses.append(ip)
    except Exception as e:
        print(f"Error getting IP addresses: {e}")

    return ip_addresses

# Data file
dataFile = os.path.join(data, f"metrics.{datetime.datetime.utcnow().isoweekday()}")

# Get basics
#eth = psutil.net_if_addrs().keys()
#ip = [addr.address for iface in eth for addr in psutil.net_if_addrs()[iface] if addr.family == socket.AF_INET and not addr.address.startswith('127.')]
ip = get_ip_addresses()
print(f'ip is {ip}')
if not ip:
    ip = "unknown"
else:
    ip = ip[0]
print(f'ip is {ip}')
product = "unknown"
version = "n/a"

# Check for CMS product
dpkg_output = os.popen('dpkg -l 2>/dev/null').read()
rpm_output = os.popen('rpm -qa 2>/dev/null').read()

if any(line.startswith("cms-") for line in dpkg_output.split('\n')) or any(line.startswith("cms-") for line in rpm_output.split('\n')):
    product = "Avaya CMS"
    version = [line.split('-')[1:] for line in (dpkg_output + rpm_output).split('\n') if line.startswith("cms-")][0]
    version = '-'.join(version)

# Get timestamp, hostname, local time
timestamp = int(time.time())
host = socket.getfqdn()
localtime = time.strftime('%Z %z')

# Get active alarms
defaultAlarmCount = -1
alarmCount = defaultAlarmCount

if os.path.exists("/cms/aom/bin/active_alarms"):
    with os.popen('/cms/aom/bin/active_alarms') as f:
        for line in f:
            if "Total" in line:
                alarmCount = int(line.split(":")[1].strip())
                break

if alarmCount == defaultAlarmCount:
    alarmCount = 0

# Write to data file
if os.path.exists(dataFile):
    with open(dataFile, 'r+') as f:
        content = f.read().rstrip()
        if content.endswith("]"):
            content = content[:-1] + ","
        else:
            content += ","
        f.seek(0)
        f.write(content)
else:
    with open(dataFile, 'w') as f:
        f.write("[")

with open(dataFile, 'a') as f:
    json.dump({
        "format": "System Info",
        "hostname": host,
        "ipaddress": ip,
        "product": product,
        "version": version,
        "localtime": localtime,
        "activeAlarms": alarmCount,
        "timestamp": timestamp
    }, f, indent=2)
    f.write("\n]\n")

