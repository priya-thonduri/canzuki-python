#!/opt/canzuki/python/3.12.4/bin/python
import subprocess
import time
from datetime import datetime
import select
import json
import requests
import os

# Define the constants
VB_CR = "\r"
VB_LF = "\n"
VB_CRLF = "\r\n"

# API endpoint (replace with the actual URL)
API_URL = "https://poc.canzuki.com/api/data"

def post_agent_counts(agent_counts):
    # Convert agent counts to JSON
    agent_counts_json = json.dumps(agent_counts)

    # Attempt to post to the API
    try:
        response = requests.post(API_URL, data=agent_counts_json, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        print("Posted agent counts to API successfully")
    except requests.RequestException as e:
        print(f"Failed to post to API: {e}")
        
        # If posting fails, save to local file
        save_to_local_file(agent_counts_json)

def save_to_local_file(agent_counts_json):
    # Ensure the data directory exists
    data_dir = os.path.join(os.getcwd(), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Get the current weekday number (0=Monday, 6=Sunday)
    weekday_num = datetime.now().weekday()
    
    # Define the filename
    filename = os.path.join(data_dir, f"agentstats.{weekday_num}")
    
    # Save the JSON data to the file
    with open(filename, "w") as file:
        file.write(agent_counts_json)
    print(f"Saved agent counts to local file: {filename}")

def run_agent():
    # Define the realTimeInput string
    real_time_input = ('do menu 0 "custom:rea:walld_a"\n'
                       'set field 1 "All Agents"\n'
                       'set field 2 "30"\n'
                       'set field 0 "0"\n'
                       'do "Run"\n'
                       'watch\n')

    # Define the commandString
    command_string = 'unset HIST_FILE\n/cms/toolsbin/clint -u cms << EOF\n' \
                     + real_time_input + 'EOF\n'

    print(f"Sent {command_string}")

    # Open a subprocess to execute the command and read output
    process = subprocess.Popen(['/bin/bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

    # Send the command to the process
    process.stdin.write(command_string)
    process.stdin.close()

    received_string = ""

    agent_count = 0
    agent_count_acw = 0
    agent_count_acd = 0
    agent_count_aux = 0
    agent_count_avail = 0

    last_print_time = time.time()

    while True:
        # Use select to wait for the output
        ready, _, _ = select.select([process.stdout], [], [], 1.0)
        if ready:
            output = process.stdout.readline()
            if output:
                received_string += output
                #print(f"Received line: {output.strip()}")

                # Process the output line for agent counts
                if len(output) > 2:
                    if output.startswith(" | "):
                        agent_count += 1
                        if "ACD" in output:
                            agent_count_acd += 1
                        if "ACW" in output:
                            agent_count_acw += 1
                        if "AVAIL" in output:
                            agent_count_avail += 1
                        if "AUX" in output:
                            agent_count_aux += 1

                if "Successful" in received_string:
                    break

        if process.poll() is not None:
            break

        # Print and post agent counts every 60 seconds
        current_time = time.time()
        if current_time - last_print_time >= 60:
            agent_counts = {
                "format": "Aura CMS",
                "agent_count": agent_count,
                "agent_count_acd": agent_count_acd,
                "agent_count_acw": agent_count_acw,
                "agent_count_avail": agent_count_avail,
                "agent_count_aux": agent_count_aux,
                "time": datetime.utcnow().isoformat()+'z',
                "timestamp": current_time
            }
            print(f"Monitor     : Date/Time {datetime.now()}")
            print(f"Agent Count: {agent_count}")
            print(f"Agent Count ACD: {agent_count_acd}")
            print(f"Agent Count ACW: {agent_count_acw}")
            print(f"Agent Count Avail: {agent_count_avail}")
            print(f"Agent Count AUX: {agent_count_aux}")
            post_agent_counts(agent_counts)
            last_print_time = current_time

    # Final print of agent counts after loop exits
    agent_counts = {
        "format": "Aura CMS",
        "agent_count": agent_count,
        "agent_count_acd": agent_count_acd,
        "agent_count_acw": agent_count_acw,
        "agent_count_avail": agent_count_avail,
        "agent_count_aux": agent_count_aux,
        "time": datetime.utcnow().isoformat()+'z',
        "timestamp": current_time
    }
    print(f"Monitor     : Date/Time {datetime.now()}")
    print(f"Agent Count: {agent_count}")
    print(f"Agent Count ACD: {agent_count_acd}")
    print(f"Agent Count ACW: {agent_count_acw}")
    print(f"Agent Count Avail: {agent_count_avail}")
    print(f"Agent Count AUX: {agent_count_aux}")
    post_agent_counts(agent_counts)

if __name__ == "__main__":
    run_agent()

