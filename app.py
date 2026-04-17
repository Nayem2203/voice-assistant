import sys
import os
import io

# 1. Compatibility Shim for Python 3.13+
try:
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop
except ImportError:
    pass

from flask import Flask, request, send_file, jsonify
from google import genai
from google.genai import types 
from gtts import gTTS
from pydub import AudioSegment

# Initialize Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
app = Flask(__name__)

def is_bangla(text):
    return any('\u0980' <= char <= '\u09FF' for char in text)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400
            
        audio_file = request.files['audio']
        audio_data = audio_file.read()

        # Brain: Ask Gemini to be a robot
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Act as a tiny, sweet pet robot. Speak in the user's language. "
                "Start with a tiny robot sound like 'Beep-boop!' or 'বিপ-বিপ!'. "
                "Keep it very short and cute (under 15 words).",
                types.Part.from_bytes(data=audio_data, mime_type='audio/wav')
            ]
        )
        bot_text = response.text
        lang_code = 'bn' if is_bangla(bot_text) else 'en'

        # Voice: Generate standard gTTS
        tts = gTTS(text=bot_text, lang=lang_code)
        temp_stream = io.BytesIO()
        tts.write_to_fp(temp_stream)
        temp_stream.seek(0)

        try:
            # Effect: Pitch Shift (The "Cute" part)
            # This requires ffmpeg to be installed on the server!
            sound = AudioSegment.from_file(temp_stream, format="mp3")
            
            # 1.2x pitch = Sweet Robot
            new_sample_rate = int(sound.frame_rate * 1.2) 
            pet_voice = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
            pet_voice = pet_voice.set_frame_rate(sound.frame_rate)
            
            output_stream = io.BytesIO()
            pet_voice.export(output_stream, format="mp3")
            output_stream.seek(0)
            return send_file(output_stream, mimetype="audio/mpeg")
            
        except Exception as effect_error:
            # If ffmpeg is missing or pydub fails, send the normal voice
            print(f"Effect failed: {effect_error}")
            temp_stream.seek(0)
            return send_file(temp_stream, mimetype="audio/mpeg")

    except Exception as e:
        print(f"General Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)