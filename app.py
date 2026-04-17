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
    return any('\u0980' <= char <= '\u09FF' for char in text)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        # 1. Personality Prompt (Cute/Pet Robot)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Act as a cute pet robot. Respond in the same language the user speaks. "
                "Be very sweet, helpful, and high-energy. Keep it under 20 words.",
                types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav')
            ]
        )
        
        bot_text = response.text
        lang_code = 'bn' if is_bangla(bot_text) else 'en'

        # 2. Generate standard voice in RAM
        tts = gTTS(text=bot_text, lang=lang_code)
        temp_stream = io.BytesIO()
        tts.write_to_fp(temp_stream)
        temp_stream.seek(0)

        # 3. CARTOON EFFECT (The Pitch Shift)
        # Load the MP3 into pydub
        sound = AudioSegment.from_file(temp_stream, format="mp3")
        
        # Shift the sample rate up to make it sound "squeaky"
        # 1.3 is "Cute Child", 1.5 is "Chipmunk/Tiny Robot"
        octaves = 0.4
        new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
        
        cartoon_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
        cartoon_sound = cartoon_sound.set_frame_rate(sound.frame_rate)

        # 4. Final Export
        output_stream = io.BytesIO()
        cartoon_sound.export(output_stream, format="mp3")
        output_stream.seek(0)

        return send_file(output_stream, mimetype="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)