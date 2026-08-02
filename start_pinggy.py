import subprocess
import time
import re

def launch_pinggy():
    print("Launching Pinggy SSH tunnel for port 8000...")
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:8000", "a.pinggy.io"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    url = None
    start = time.time()
    while time.time() - start < 15:
        line = proc.stdout.readline()
        if line:
            print("Pinggy Output:", line.strip())
            match = re.search(r'https://[a-zA-Z0-9\.-]+\.free\.pinggy\.link', line)
            if match:
                url = match.group(0)
                break
        time.sleep(0.5)
        
    return url

if __name__ == "__main__":
    url = launch_pinggy()
    print("PINGGY_URL:", url)
