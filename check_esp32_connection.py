import socket
import sys
import os

# Try to load config if possible
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import camera.config as cfg
    host = cfg.ESP32_HOST
    port = cfg.ESP32_PORT
except:
    host = "192.168.4.1"
    port = 3333

def check_connection(host, port, timeout=5):
    print(f"Checking connection to ESP32 at {host}:{port}...")
    try:
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Connect to the server
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print(f"[✓] SUCCESS: Connected to {host}:{port}")
            sock.close()
            return True
        else:
            print(f"[!] FAILED: Could not connect to {host}:{port} (Error code: {result})")
            print("Tip: Make sure you are connected to the ESP32's Wi-Fi network.")
            return False
    except Exception as e:
        print(f"[!] ERROR: {e}")
        return False

if __name__ == "__main__":
    if not check_connection(host, port):
        sys.exit(1)
    sys.exit(0)
