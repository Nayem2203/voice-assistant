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

# ================== HELPER ==================
def is_bangla(text):
    return any('\u0980' <= c <= '\u09FF' for c in text)

# ================== ROUTES ==================

@app.route('/')
def home():
    return "✅ Server is running!"

@app.route('/process', methods=['POST'])
def process_audio():
    try:
        print("\n==============================")
        print("➡ Incoming Request")
        print("==============================")

        # -------- RECEIVE AUDIO --------
        if request.data:
            audio_bytes = request.data
            print("📡 Source: ESP32 RAW")
        elif 'audio' in request.files:
            audio_bytes = request.files['audio'].read()
            print("📱 Source: Mobile Upload")
        else:
            print("❌ No audio received")
            return jsonify({"error": "No audio"}), 400

        print(f"📦 Audio size: {len(audio_bytes)} bytes")

        # -------- GEMINI --------
        print("🤖 Sending to Gemini...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "You are a tiny robot. Reply short. Start with Beep!",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            ]
        )

        bot_text = response.text.strip()
        print("💬 Gemini reply:", bot_text)

        # -------- TTS --------
        lang = "bn" if is_bangla(bot_text) else "en"

        tts = gTTS(text=bot_text, lang=lang)

        mp3_stream = io.BytesIO()
        tts.write_to_fp(mp3_stream)
        mp3_stream.seek(0)

        print("🔊 Converting to WAV...")

        sound = AudioSegment.from_file(mp3_stream, format="mp3")
        sound = sound.set_frame_rate(16000)
        sound = sound.set_channels(1)
        sound = sound.set_sample_width(2)

        # cartoon effect
        new_rate = int(sound.frame_rate * 1.25)
        sound = sound._spawn(sound.raw_data, overrides={"frame_rate": new_rate})
        sound = sound.set_frame_rate(16000)

        # -------- EXPORT --------
        output = io.BytesIO()
        sound.export(output, format="wav")
        output.seek(0)

        print(f"📤 Sending response: {output.getbuffer().nbytes} bytes")
        print("==============================\n")

        return send_file(
            output,
            mimetype="audio/wav",
            as_attachment=False
        )

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Running on port {port}")
    app.run(host="0.0.0.0", port=port)