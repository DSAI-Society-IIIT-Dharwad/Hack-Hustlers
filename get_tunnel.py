import subprocess
import re
import threading
import time
import os

if os.path.exists('url.txt'):
    os.remove('url.txt')

p = subprocess.Popen(['cloudflared.exe', 'tunnel', '--url', 'http://localhost:5000'], stderr=subprocess.PIPE, text=True, encoding='utf-8')

def read_output():
    for line in iter(p.stderr.readline, ''):
        match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
        if match:
            with open("url.txt", "w") as f:
                f.write(match.group(1))
            break

t = threading.Thread(target=read_output)
t.daemon = True
t.start()

time.sleep(8)
