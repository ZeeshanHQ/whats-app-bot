import time
import sys
from pyngrok import ngrok

print("Starting ngrok tunnel on port 8000...", flush=True)
tunnel = ngrok.connect(8000)
print(f"NGROK_URL={tunnel.public_url}", flush=True)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.disconnect(tunnel.public_url)
