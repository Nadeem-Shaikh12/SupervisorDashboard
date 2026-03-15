import requests

ip = "192.168.4.1"
port = 80
endpoints = [
    "/",
    "/mjpeg/1",
    "/stream",
    "/capture",
    "/video",
    "/axis-cgi/mjpg/video.cgi",
    "/img/video.mjpeg",
    "/cam-hi.jpg",
    "/81c/stream",
    "/camera",
    "/live"
]

def scan_endpoints():
    print(f"Scanning HTTP endpoints on {ip}:{port}...")
    for ep in endpoints:
        url = f"http://{ip}:{port}{ep}"
        try:
            res = requests.get(url, timeout=2, stream=True)
            print(f"[HTTP {res.status_code}] {url}")
            if res.status_code == 200:
                print(f"  Content-Type: {res.headers.get('Content-Type')}")
            res.close()
        except Exception as e:
            # print(f"[ERROR] {url} - {e}")
            pass

if __name__ == "__main__":
    scan_endpoints()
