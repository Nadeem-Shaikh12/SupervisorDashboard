import cv2
import time

def test_reader_capture():
    stream_url = "http://127.0.0.1:8001/stream"
    print(f"Attempting to open stream with VideoCapture: {stream_url}")
    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("FAILED: VideoCapture could not open stream.")
        return
    
    print("VideoCapture opened. Waiting for frame...")
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS: Frame captured! Shape: {frame.shape}")
        cv2.imwrite("data/reader_test_capture.jpg", frame)
    else:
        print("FAILED: Could not read frame from open VideoCapture.")
    
    cap.release()

if __name__ == "__main__":
    test_reader_capture()
