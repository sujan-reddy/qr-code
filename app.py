from flask import Flask, render_template, Response, request, jsonify
import cv2
from pyzbar import pyzbar
import numpy as np
import threading

# Initialize Flask app
app = Flask(__name__)

# Global variable to store the latest QR code data
latest_qr_code = None
# Lock to ensure thread-safe access to the latest_qr_code variable
lock = threading.Lock()

# Function to decode QR codes from a frame
def decode_qr(frame):
    global latest_qr_code
    # Decode QR codes from the frame
    decoded_objects = pyzbar.decode(frame)
    for obj in decoded_objects:
        # Extract the QR code data
        qr_data = obj.data.decode("utf-8")
        with lock:
            # Save only if it is a new QR code
            if latest_qr_code != qr_data:
                latest_qr_code = qr_data
                # Save the QR code data to a file
                save_qr_code(qr_data)

        # Draw bounding box around the QR code
        points = obj.polygon
        if len(points) > 4:
            # Use convex hull to simplify the bounding box
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            hull = list(map(tuple, np.squeeze(hull)))
        else:
            hull = points
        n = len(hull)
        # Draw the bounding box
        for j in range(0, n):
            cv2.line(frame, hull[j], hull[(j + 1) % n], (0, 255, 0), 3)
        # Display the QR code data on the frame
        cv2.putText(frame, qr_data, (obj.rect.left, obj.rect.top), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    return cv2.flip(frame, 1)  # Flip the frame horizontally

# Function to save the QR code data to a file
def save_qr_code(qr_data):
    with open('scanned_codes.txt', 'a') as file:
        file.write(f"{qr_data}\n")

# Generator function to yield frames from the camera
def generate_frames():
    # Open the camera
    cap = cv2.VideoCapture(0)
    while True:
        # Read a frame from the camera
        success, frame = cap.read()
        if not success:
            break
        else:
            # Decode QR codes from the frame
            frame = decode_qr(frame)
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Yield the frame as a multipart response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to get the latest QR code data
@app.route('/get_latest_qr', methods=['GET'])
def get_latest_qr():
    global latest_qr_code
    with lock:
        return jsonify({'qr_code': latest_qr_code})

# Run the Flask app
if __name__ == '__main__':
    app.run()
