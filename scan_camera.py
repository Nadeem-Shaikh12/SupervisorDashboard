import socket
import threading
from queue import Queue
import time

# Scan parameters
TARGET_SUBNET = "192.168.4"
TARGET_PORTS = [3333, 80, 81, 8080]
THREADS = 50
TIMEOUT = 0.5

def scan_port(ip, port, results):
    """Attempt to connect to a specific port on an IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            if s.connect_ex((ip, port)) == 0:
                results.append((ip, port))
    except (socket.timeout, socket.error):
        pass

def worker(queue, results):
    """Worker thread to process the scan queue."""
    while not queue.empty():
        ip, port = queue.get()
        scan_port(ip, port, results)
        queue.task_done()

def main():
    print(f"--- Starting DreamVision Camera Discovery ---")
    print(f"Scanning subnet {TARGET_SUBNET}.0/24 on ports {TARGET_PORTS}...")
    
    scan_queue = Queue()
    results = []
    
    # Fill the queue with all IP/port combinations in the subnet
    for i in range(1, 255):
        ip = f"{TARGET_SUBNET}.{i}"
        for port in TARGET_PORTS:
            scan_queue.put((ip, port))
            
    # Start worker threads
    start_time = time.time()
    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker, args=(scan_queue, results), daemon=True)
        t.start()
        threads.append(t)
        
    # Wait for completion
    scan_queue.join()
    end_time = time.time()
    
    print(f"\nScan completed in {end_time - start_time:.2f} seconds.")
    if results:
        print(f"Found {len(results)} potential camera(s):")
        for ip, port in results:
            print(f" [+] {ip}:{port}")
    else:
        print("No cameras found on this subnet. Ensure you are connected to the ESP32 WiFi.")

if __name__ == "__main__":
    main()
