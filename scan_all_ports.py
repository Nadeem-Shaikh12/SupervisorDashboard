import socket
from concurrent.futures import ThreadPoolExecutor

ip = "192.168.4.1"

def scan_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex((ip, port))
    sock.close()
    if result == 0:
        print(f"[OPEN] Port {port}")

def run_scan():
    print(f"Scanning ports on {ip}...")
    ports_to_scan = list(range(1, 10000))
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(scan_port, ports_to_scan)
    print("Scan complete.")

if __name__ == "__main__":
    run_scan()
