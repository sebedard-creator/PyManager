import time
import sys

print("Starting dummy worker...", flush=True)

count = 0
while True:
    count += 1
    print(f"[{time.strftime('%X')}] Dummy log output line {count}", flush=True)
    
    # Simulate some errors randomly
    if count % 5 == 0:
        print(f"[{time.strftime('%X')}] Simulated error at step {count}", file=sys.stderr, flush=True)
        
    time.sleep(2)
