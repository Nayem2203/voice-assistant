import sys
try:
    import audioop_lts as audioop
    sys.modules['audioop'] = audioop
except ImportError:
    pass

import os
import io
from flask import Flask, request, send_file, jsonify
from google import genai
from google.genai import types 
from gtts import gTTS
from pydub import AudioSegment

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
app = Flask(__name__)

def is_bangla(text):
    return any('\u0980' <= char <= '\u09FF' for char in text)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        audio_file = request.files['audio']
        
        # 1. THE BRAIN: Cute Robot Personality
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "You are a tiny, sweet pet robot. Speak in the user's language. "
                "Start with a tiny robot sound like 'Beep!' or 'Boop!'. "
                "Keep it very short and cute (under 15 words).",
                types.Part.from_bytes(data=audio_file.read(), mime_type='audio/wav')
            ]
        )
        
        bot_text = response.text
        lang_code = 'bn' if is_bangla(bot_text) else 'en'

        # 2. THE VOICE: Generate standard speech
        tts = gTTS(text=bot_text, lang=lang_code)
        temp_stream = io.BytesIO()
        tts.write_to_fp(temp_stream)
        temp_stream.seek(0)

        # 3. THE MAGIC: Pitch Up, Speed Normal
        sound = AudioSegment.from_file(temp_stream, format="mp3")
        
        # This shifts the pitch up (Cute/Tiny effect) without speeding it up
        new_sample_rate = int(sound.frame_rate * 1.3) 
        pet_voice = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        pet_voice = pet_voice.set_frame_rate(sound.frame_rate)

        output_stream = io.BytesIO()
        pet_voice.export(output_stream, format="mp3")
        output_stream.seek(0)

        return send_file(output_stream, mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))