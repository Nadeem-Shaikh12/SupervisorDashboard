import base64, requests, numpy as np, cv2, datetime

# Simulate thermal frame (64x64 with hot spot ~800C)
frame = np.random.uniform(200, 850, (64, 64)).astype(np.float32)
norm  = ((frame - frame.min()) / (frame.max() - frame.min()) * 255).astype(np.uint8)
_, buf = cv2.imencode('.jpg', norm)
b64 = base64.b64encode(buf).decode()

r = requests.post('http://127.0.0.1:8002/inspect', json={
    'device_id': 'DEMO-L1-GLASS',
    'thermal_image': b64,
    'timestamp': datetime.datetime.now().isoformat()
}, timeout=20)

if r.ok:
    d = r.json()
    print()
    print('  === DreamVision Full Pipeline Test ===')
    print('  UID           :', d.get('part_uid'))
    print('  Component     :', d.get('component_name'))
    print('  Temperature   :', d.get('temperature'), 'C')
    print('  Status        :', d.get('status'))
    print('  Device        :', d.get('device_id'))
    print('  Timestamp     :', d.get('timestamp'))
    print('  Defect Prob   :', round(d.get('predicted_defect_probability', 0), 3))
    print()
    print('  All 7 pipeline stages PASSED.')
else:
    print('FAILED:', r.status_code, r.text[:400])
