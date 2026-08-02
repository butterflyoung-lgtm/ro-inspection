import subprocess
import time
import re
import os

def launch_tunnel():
    print("Launching localtunnel for port 8000...")
    cmd = ["cmd.exe", "/c", "npx", "-y", "localtunnel", "--port", "8000"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    url = None
    start = time.time()
    while time.time() - start < 15:
        line = proc.stdout.readline()
        if line:
            print("Tunnel Output:", line.strip())
            match = re.search(r'https://[a-zA-Z0-9\.-]+\.loca\.lt', line)
            if match:
                url = match.group(0)
                break
        time.sleep(0.5)
        
    return url

if __name__ == "__main__":
    url = launch_tunnel()
    print("RESULT_URL:", url)
