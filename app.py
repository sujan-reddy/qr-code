from flask import Flask, render_template, Response, jsonify
import cv2
from pyzbar import *
import numpy as np
import threading

app = Flask(__name__)

# Global variable to store the latest QR code data
latest_qr_code = None
lock = threading.Lock()

# Function to decode QR codes from a frame
def decode_qr(frame):
    global latest_qr_code
    decoded_objects = pyzbar.decode(frame)
    if decoded_objects:
        qr_data = decoded_objects[0].data.decode('utf-8')
        with lock:
            if latest_qr_code != qr_data:  # Save only if it is a new QR code
                latest_qr_code = qr_data
                save_qr_code(qr_data)
        return qr_data
    return None

# Function to save the QR code data to a file
def save_qr_code(qr_data):
    with open('scanned_codes.txt', 'a') as file:
        file.write(f"{qr_data}\n")

# Generator function to yield frames from the camera
def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            qr_data = decode_qr(frame)
            if qr_data:
                # Draw bounding box around the QR code
                cv2.putText(frame, qr_data, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route for the index page
@app.route('/')
def index():
    global latest_qr_code
    with lock:
        qr_code = latest_qr_code
    return render_template('index.html', qr_code=qr_code)

# Route for the video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
