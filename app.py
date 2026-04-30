# ================== COMPATIBILITY FIX ==================
import sys
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        print("audioop missing")

# ================== IMPORTS ==================
import os
import io
from flask import Flask, request, send_file, jsonify

from google import genai
from google.genai import types

from gtts import gTTS
from pydub import AudioSegment

# ================== SETUP ==================
app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# ================== LANGUAGE DETECTION ==================
def is_bangla(text):
    return any('\u0980' <= c <= '\u09FF' for c in text)

# ================== MAIN ROUTE ==================
@app.route('/process', methods=['POST'])
def process_audio():
    try:
        # 1. CHECK AUDIO
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()

        print("🎤 Received audio from ESP32")

        # ================== 2. GEMINI PROCESS ==================
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "You are a tiny cute robot. Reply very short (max 10 words). Start with Beep!",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            ]
        )

        bot_text = response.text.strip()
        print("🤖 Bot:", bot_text)

        # ================== 3. TEXT TO SPEECH ==================
        lang = "bn" if is_bangla(bot_text) else "en"

        tts = gTTS(text=bot_text, lang=lang)

        mp3_stream = io.BytesIO()
        tts.write_to_fp(mp3_stream)
        mp3_stream.seek(0)

        # ================== 4. CONVERT TO WAV ==================
        sound = AudioSegment.from_file(mp3_stream, format="mp3")

        # Normalize format for ESP32
        sound = sound.set_frame_rate(16000)
        sound = sound.set_channels(1)
        sound = sound.set_sample_width(2)  # 16-bit

        # ================== 5. CARTOON VOICE ==================
        new_sample_rate = int(sound.frame_rate * 1.25)

        cartoon = sound._spawn(
            sound.raw_data,
            overrides={"frame_rate": new_sample_rate}
        ).set_frame_rate(16000)

        # ================== 6. EXPORT WAV ==================
        output = io.BytesIO()
        cartoon.export(output, format="wav")
        output.seek(0)

        print("🔊 Sending response to ESP32")

        return send_file(
            output,
            mimetype="audio/wav",
            as_attachment=False,
            download_name="response.wav"
        )

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Server running on port {port}")
    app.run(host="0.0.0.0", port=port)