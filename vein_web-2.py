import cv2
import numpy as np
import subprocess
import time
from flask import Flask, Response

# --- CONFIGURATION ---
# Back to 640x480 (The Sweet Spot for Pi 4/3B+)
CAMERA_CMD = [
    "rpicam-vid", "-t", "0",
    "--inline",
    "--width", "640", "--height", "480",
    "--codec", "mjpeg",
    "--listen", "-o", "tcp://0.0.0.0:8888"
]

app = Flask(__name__)

# --- 1. THE BRAIN: Detection Logic ---
def classify_anomalies(frame):
    # Performance Hack: Process a smaller version of the image
    # We resize to 320x240 just for the math, then draw on the original 640x480
    small_frame = cv2.resize(frame, (320, 240))
    gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
    
    # CLAHE: It makes veins visible.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # Thresholding
    _, mask = cv2.threshold(enhanced, 85, 255, cv2.THRESH_BINARY_INV)
    
    # Simple Noise Reduction (Fast)
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find Contours on the small image
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    output_frame = frame.copy()
    
    # Scale factor to map small coordinates back to big image
    scale_x = frame.shape[1] / small_frame.shape[1]
    scale_y = frame.shape[0] / small_frame.shape[0]

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100: continue  # Ignore tiny noise (adjusted for small res)
        
        # Scale the contour points back up to 640x480
        cnt_big = cnt.astype(float)
        cnt_big[:, :, 0] *= scale_x
        cnt_big[:, :, 1] *= scale_y
        cnt_big = cnt_big.astype(np.int32)

        # Calculate Shape Features
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0: continue
        
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        x, y, w, h = cv2.boundingRect(cnt_big)
        aspect_ratio = float(w)/h if h > w else float(h)/w
        
        # --- DECISION LOGIC ---
        if circularity < 0.4 or aspect_ratio > 2.5:
            # VEIN (Green)
            cv2.drawContours(output_frame, [cnt_big], -1, (0, 255, 0), 2)
            cv2.putText(output_frame, "VEIN", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        elif circularity > 0.6:
            # HEMATOMA (Red)
            cv2.rectangle(output_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(output_frame, "HEMATOMA", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
    return output_frame

# --- 2. THE STREAMER ---
def generate_frames():
    cap = cv2.VideoCapture('tcp://127.0.0.1:8888') 
    time.sleep(1.0)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
            
        try:
            processed_frame = classify_anomalies(frame)
            
            # Quality 80% is the balance between Clear and Fast
            ret, buffer = cv2.imencode('.jpg', processed_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
        except Exception as e:
            pass

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>VeinX Diagnostic System</title>
        <style>
            body { background-color: #1a1a1a; color: white; font-family: sans-serif; text-align: center; }
            h1 { color: #00ff00; margin-bottom: 5px; }
            img { border: 5px solid #333; border-radius: 10px; max-width: 100%; box-shadow: 0 0 20px rgba(0,255,0,0.2); }
        </style>
    </head>
    <body>
        <h1>VeinX: Balanced Mode</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Starting Camera Driver (Balanced Mode)...")
    camera_process = None
    try:
        camera_process = subprocess.Popen(CAMERA_CMD)
        time.sleep(3)
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        if camera_process:
            camera_process.terminate()

            
# ssh abhinav@raspy.local       

# python vein_web.py 