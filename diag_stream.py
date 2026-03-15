import requests
import time

def check_stream():
    url = "http://localhost:8001/stream"
    print(f"Checking stream at {url}...")
    try:
        # Just try to get the first few bytes to see if it responds
        with requests.get(url, stream=True, timeout=5) as r:
            print(f"Status Code: {r.status_code}")
            print(f"Headers: {r.headers}")
            if r.status_code == 200:
                print("Stream is UP. Reading first chunk...")
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        print(f"Read {len(chunk)} bytes. Stream is ACTIVE.")
                        break
            else:
                print(f"Stream returned non-200 status: {r.status_code}")
    except Exception as e:
        print(f"Stream check FAILED: {e}")

if __name__ == "__main__":
    check_stream()
