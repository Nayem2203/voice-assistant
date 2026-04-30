import sys
import time
import threading
import os
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# 🔁 Track last request time
last_request_time = time.time()


# ✅ Root route (fix 404 issue)
@app.route("/")
def home():
    return "✅ Voice Server is Running!"


# 🔊 Log every request
@app.before_request
def log_request():
    global last_request_time
    last_request_time = time.time()
    print("\n==============================")
    print(f"➡ Incoming: {request.method} {request.url}")
    print("==============================")


# 🎤 Upload route (ESP32 sends audio here)
@app.route("/upload", methods=["POST"])
def upload():

    if 'file' not in request.files:
        print("❌ No file received!")
        return jsonify({"status": "fail", "message": "No file"}), 400

    file = request.files['file']

    if file.filename == '':
        print("❌ Empty file!")
        return jsonify({"status": "fail", "message": "Empty file"}), 400

    print("✅ File received from ESP32!")

    # 💾 Save file
    file_path = "received.wav"
    file.save(file_path)

    # 📊 File size check
    file_size = os.path.getsize(file_path)
    print(f"📦 File size: {file_size} bytes")

    # ⚠ If file too small
    if file_size < 100:
        print("⚠ Warning: Audio file too small!")

    # 🧠 ===== PROCESS HERE =====
    # You can add:
    # - Speech to text
    # - AI response
    # - Text to speech

    # For now: dummy response file
    response_audio = "response.wav"

    # If no response file exists → create dummy
    if not os.path.exists(response_audio):
        with open(response_audio, "wb") as f:
            f.write(b'\x00\x00')  # placeholder

    print("🔊 Sending response back to ESP32...")

    return send_file(response_audio, mimetype="audio/wav")


# ⏱ Monitor if no data received
def monitor():
    global last_request_time
    while True:
        if time.time() - last_request_time > 10:
            print("⚠ No data received in last 10 seconds")
        time.sleep(5)


# 🚀 Start monitor thread
threading.Thread(target=monitor, daemon=True).start()


# ▶ Run server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server starting on port {port}...")
    app.run(host="0.0.0.0", port=port)