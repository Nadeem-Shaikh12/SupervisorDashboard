import requests
import time

def check_health():
    services = {
        "Capture API (8001)": "http://localhost:8001/status",
        "Edge Server (8002)": "http://localhost:8002/inspections"
    }
    
    for name, url in services.items():
        try:
            res = requests.get(url, timeout=2)
            print(f"{name}: [UP] (Status: {res.status_code})")
            if "8001" in url:
                print(f"  Capture Details: {res.json()}")
        except Exception as e:
            print(f"{name}: [DOWN] ({e})")

if __name__ == "__main__":
    check_health()
