import base64, requests, numpy as np, cv2, datetime, time

results = []
for i in range(5):
    frame = np.random.uniform(50 + i * 150, 900, (64, 64)).astype(np.float32)
    norm = ((frame - frame.min()) / (frame.max() - frame.min()) * 255).astype(np.uint8)
    _, buf = cv2.imencode('.jpg', norm)
    b64 = base64.b64encode(buf).decode()
    r = requests.post('http://127.0.0.1:8002/inspect', json={
        'device_id': 'L1-GLASS-01',
        'thermal_image': b64,
        'timestamp': datetime.datetime.now().isoformat()
    }, timeout=15)
    if r.ok:
        d = r.json()
        uid    = d.get('part_uid', '?')
        status = d.get('status', '?')
        temp   = d.get('temperature', 0)
        print('  Inspection', i + 1, '| UID:', uid, '| Status:', status, '| Temp:', temp, 'C')
    else:
        print('  Inspection', i + 1, 'FAILED', r.status_code)
    time.sleep(0.5)

print()
print('All 5 inspections complete. Dashboard should now show live data.')
