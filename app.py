# ================== IMPORTS ==================
import sys
import os
import io
from flask import Flask, request, send_file, jsonify

# audioop fix
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop

from google import genai
from google.genai import types
from gtts import gTTS
from pydub import AudioSegment

# ================== SETUP ==================
app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
print("🔑 API KEY:", "OK" if API_KEY else "MISSING")

client = genai.Client(api_key=API_KEY)

# ================== ROUTES ==================
@app.route('/')
def home():
    return "✅ Server running"

@app.route('/process', methods=['POST'])
def process_audio():
    try:
        print("\n==============================")
        print("➡ Incoming request")

        # -------- RECEIVE --------
        if request.data:
            audio_bytes = request.data
            print("📡 Source: ESP32 RAW")
        elif 'audio' in request.files:
            audio_bytes = request.files['audio'].read()
            print("📱 Source: file upload")
        else:
            print("❌ No audio")
            return jsonify({"error": "No audio"}), 400

        print(f"📦 Size: {len(audio_bytes)} bytes")

        # show first few bytes (debug)
        print("🔍 First 20 bytes:", audio_bytes[:20])

        # -------- GEMINI --------
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Reply very short (max 8 words). Start with Beep!",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            ]
        )

        bot_text = response.text.strip()
        print("🤖 Reply:", bot_text)

        # -------- TTS --------
        tts = gTTS(text=bot_text, lang="en")

        mp3 = io.BytesIO()
        tts.write_to_fp(mp3)
        mp3.seek(0)

        sound = AudioSegment.from_file(mp3, format="mp3")

        # normalize for ESP32
        sound = sound.set_frame_rate(16000)
        sound = sound.set_channels(1)
        sound = sound.set_sample_width(2)

        # -------- EXPORT WAV --------
        out = io.BytesIO()
        sound.export(out, format="wav")
        out.seek(0)

        print(f"📤 Sending back: {out.getbuffer().nbytes} bytes")
        print("==============================\n")

        return send_file(out, mimetype="audio/wav")

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)