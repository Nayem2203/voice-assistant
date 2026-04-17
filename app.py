import os
import io
from flask import Flask, request, send_file, jsonify
from google import genai
from google.genai import types 
from gtts import gTTS

# Setup Client
MY_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=MY_API_KEY)

app = Flask(__name__)

def is_bangla(text):
    # Checks if the text contains characters in the Bengali Unicode range
    return any('\u0980' <= char <= '\u09FF' for char in text)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        print("Gemini is listening...")
        
        # 1. Multi-language Prompt
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Listen to the audio. Response as you are friend"
                "If they speak Bangla, respond in natural Bangla. If English, respond in English. "
                "Keep the response brief (under 20 words).",
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type='audio/wav'
                )
            ]
        )
        
        bot_text = response.text
        print(f"Bot response: {bot_text}")

        # 2. Dynamic Language Selection for Voice
        lang_code = 'bn' if is_bangla(bot_text) else 'en'
        print(f"Using voice language: {lang_code}")

        # 3. Voice Generation in RAM
        tts = gTTS(text=bot_text, lang=lang_code)
        audio_stream = io.BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)

        return send_file(
            audio_stream, 
            mimetype="audio/mpeg", 
            as_attachment=False, 
            download_name="response.mp3"
        )

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)