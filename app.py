# ================== IMPORTS ==================
import sys
import os
import io
from flask import Flask, request, send_file, jsonify

try:
    import audioop
except ImportError:
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop

from google import genai
from google.genai import types
from gtts import gTTS
from pydub import AudioSegment

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

# ================== HELPER ==================
def is_bangla(text):
    return any('\u0980' <= c <= '\u09FF' for c in text)

# ================== ROUTES ==================

@app.route('/')
def home():
    return "Server OK"

@app.route('/process', methods=['POST'])
def process_audio():
    try:
        print("\n====== NEW REQUEST ======")

        # -------- RECEIVE AUDIO --------
        if request.data:
            audio_bytes = request.data
            print("📡 ESP32 RAW audio received")
        else:
            return jsonify({"error": "No audio"}), 400

        print("📦 Size:", len(audio_bytes))

        # -------- SPEECH TO TEXT --------
        print("🧠 Converting speech to text...")

        stt_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Convert this speech to text only.",
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            ]
        )

        user_text = stt_response.text.strip()
        print("🗣 User said:", user_text)

        # -------- GENERATE RESPONSE --------
        print("🤖 Generating reply...")

        reply = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                f"User said: {user_text}. Reply short and friendly."
            ]
        )

        bot_text = reply.text.strip()
        print("💬 Bot reply:", bot_text)

        # -------- TEXT TO SPEECH --------
        lang = "bn" if is_bangla(bot_text) else "en"

        tts = gTTS(text=bot_text, lang=lang)

        mp3_stream = io.BytesIO()
        tts.write_to_fp(mp3_stream)
        mp3_stream.seek(0)

        # convert to WAV
        sound = AudioSegment.from_file(mp3_stream, format="mp3")
        sound = sound.set_frame_rate(16000)
        sound = sound.set_channels(1)
        sound = sound.set_sample_width(2)

        output = io.BytesIO()
        sound.export(output, format="wav")
        output.seek(0)

        print("🔊 Sending audio back\n")

        return send_file(output, mimetype="audio/wav")

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)