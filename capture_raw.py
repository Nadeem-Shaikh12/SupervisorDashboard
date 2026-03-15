import requests

def capture_raw_stream():
    url = "http://127.0.0.1:8001/stream"
    print(f"Capturing raw stream from {url}...")
    try:
        with requests.get(url, stream=True, timeout=5) as r:
            with open("data/raw_stream.bin", "wb") as f:
                count = 0
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)
                    count += len(chunk)
                    if count > 50000: # Capture ~50KB
                        break
        print(f"Captured {count} bytes to data/raw_stream.bin")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    capture_raw_stream()
