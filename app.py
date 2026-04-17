# --- THE COMPATIBILITY SHIM (MUST BE AT THE VERY TOP) ---
import sys
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        print("Warning: audioop-lts not found. Cartoon effect may fail.")

import os
import io
from flask import Flask, request, send_file, jsonify
from google import genai
from google.genai import types 
from gtts import gTTS
from pydub import AudioSegment

# Setup Client
MY_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=MY_API_KEY)

app = Flask(__name__)

def is_bangla(text):
    """Detects if string contains Bengali characters."""
    return any('\u0980' <= char <= '\u09FF' for char in text)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        print("Gemini is listening...")
        
        # 1. Multi-language Personality Prompt
        # We tell Gemini to act cute and match the user's language
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Act as a cute pet robot. Respond in the same language as the user. "
                "Be sweet, helpful, and very brief (under 20 words).",
                types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav')
            ]
        )
        
        bot_text = response.text
        print(f"Bot says: {bot_text}")

        # 2. Select voice language
        lang_code = 'bn' if is_bangla(bot_text) else 'en'

        # 3. Generate voice in RAM
        tts = gTTS(text=bot_text, lang=lang_code)
        temp_stream = io.BytesIO()
        tts.write_to_fp(temp_stream)
        temp_stream.seek(0)

        # 4. THE CARTOON EFFECT (Pitch Shifting)
        # Load audio and increase sample rate to make it squeaky
        sound = AudioSegment.from_file(temp_stream, format="mp3")
        
        # 0.4 octaves up = Cute Robot/Child. 0.6 = Chipmunk.
        octaves = 0.4 
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        
        # Apply the pitch shift
        cartoon_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        cartoon_sound = cartoon_sound.set_frame_rate(sound.frame_rate)

        # 5. Export back to stream
        output_stream = io.BytesIO()
        cartoon_sound.export(output_stream, format="mp3")
        output_stream.seek(0)

        return send_file(
            output_stream, 
            mimetype="audio/mpeg", 
            as_attachment=False, 
            download_name="response.mp3"
        )

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)