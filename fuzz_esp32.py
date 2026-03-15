import socket
import time

host = "192.168.4.1"
port = 3333

def try_command(val_str):
    print(f"\n--- Trying Val: {val_str} ---")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        payload_str = f"000CWREGB1{val_str}"
        payload = payload_str.encode()
        crc = sum(payload) & 0xFFFF
        cmd = b"   #" + payload + f"{crc:04X}".encode()
        
        print(f"Sending: {cmd}")
        sock.sendall(cmd)

        start_time = time.time()
        total_bytes = 0
        while time.time() - start_time < 3:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                total_bytes += len(data)
                print(f"Received {len(data)} bytes. (Total: {total_bytes})")
            except socket.timeout:
                break
        
        sock.close()
        print(f"Result for {val_str}: {total_bytes} bytes received.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    for v in ["00", "01", "02", "03", "04", "05", "06", "07"]:
        try_command(v)
