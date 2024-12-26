import os
import cv2
from flask import Flask, render_template, request, redirect, send_file, url_for, Response
from werkzeug.utils import secure_filename
from ultralytics import YOLO

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv'}  # Video formats
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Max file size 100MB

model = YOLO("ppe.pt")  # Load YOLO model


# Helper function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Route to render the dashboard with upload options
@app.route('/')
def index():
    return render_template('dashboard.html')


# Route to upload video file
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Perform detection on the uploaded video
            return redirect(url_for('process_video', filepath=filepath))
    return render_template('upload.html')


# Process the uploaded video
@app.route('/process_video')
def process_video():
    filepath = request.args.get('filepath')
    if not filepath:
        return redirect(url_for('index'))

    def generate_frames():
        cap = cv2.VideoCapture(filepath)
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Perform detection on each frame
            results = model(frame)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # Extract bounding box coordinates and class info
                    x1, y1, x2, y2 = box.xyxy[0]
                    conf = box.conf[0]
                    cls = int(box.cls[0])
                    currentClass = model.names[cls]

                    # Convert bounding box coordinates to integers
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    # Draw bounding box with different colors based on the detection class
                    if currentClass == "ppe" and conf > 0.5:
                        # Green for PPE detection
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{currentClass} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    elif currentClass != "ppe" and conf > 0.5:
                        # Red for non-PPE detection
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, f"{currentClass} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Encode the frame to JPEG for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        cap.release()

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Route to handle webcam feed (optional)
@app.route('/video_feed')
def video_feed():
    def gen_frames():
        cap = cv2.VideoCapture(0)  # Use default webcam
        while True:
            success, frame = cap.read()
            if not success:
                break
            results = model(frame, stream=True)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    conf = box.conf[0]
                    cls = int(box.cls[0])
                    currentClass = model.names[cls]

                    # Convert bounding box coordinates to integers
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    # Color coding based on class
                    if currentClass == "ppe" and conf > 0.5:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green for PPE
                        cv2.putText(frame, f"{currentClass} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    elif currentClass != "ppe" and conf > 0.5:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red for non-PPE
                        cv2.putText(frame, f"{currentClass} {conf:.2f}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam')
def webcam():
    return render_template('webcam.html')

if __name__ == "__main__":
    app.run(debug=True)


