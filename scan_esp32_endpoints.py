import requests
import socket

ip = "192.168.4.1"
ports = [80, 81, 8000, 3333]
endpoints = ["/stream", "/capture", "/mjpeg", ""]

def scan():
    print(f"Scanning {ip}...")
    for port in ports:
        # Check if port is open first
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            print(f"[✓] Port {port} is OPEN")
            for ep in endpoints:
                url = f"http://{ip}:{port}{ep}"
                try:
                    res = requests.get(url, timeout=2, stream=True)
                    print(f"    - Endpoint {url}: Status {res.status_code}")
                    if res.status_code == 200:
                        print(f"      [!!!] FOUND STREAMING ENDPOINT: {url}")
                        # Peek at headers
                        print(f"      Content-Type: {res.headers.get('Content-Type')}")
                        res.close()
                except Exception as e:
                    # print(f"    - Endpoint {url}: Error {e}")
                    pass
        else:
            print(f"[ ] Port {port} is CLOSED")
        sock.close()

if __name__ == "__main__":
    scan()
