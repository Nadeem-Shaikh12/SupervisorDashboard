import socket
import sys
import time

host = "192.168.4.1"
port = 3333

def debug_raw():
    print(f"Connecting to ESP32 at {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("[✓] TCP Connected.")

        # Send the start command
        # Waveshare command: 000CWREG B1 03
        # payload = b"000CWREGB103"
        # crc = sum(payload) & 0xFFFF
        # cmd = b"   #" + payload + f"{crc:04X}".encode()
        # print(f"Sending command: {cmd}")
        # sock.sendall(cmd)

        print("Waiting for data (15s timeout)...")
        start_time = time.time()
        total_bytes = 0
        while time.time() - start_time < 15:
            try:
                data = sock.recv(4096)
                if not data:
                    print("Connection closed by peer.")
                    break
                total_bytes += len(data)
                print(f"Received {len(data)} bytes (Total: {total_bytes})")
                if total_bytes < 100:
                    print(f"Data snippet: {data.hex()[:50]}")
            except socket.timeout:
                print("Read timeout - no data received in 10s.")
                break
        
        print(f"Finished. Total bytes received: {total_bytes}")
        sock.close()
    except Exception as e:
        print(f"[!] ERROR: {e}")

if __name__ == "__main__":
    debug_raw()
