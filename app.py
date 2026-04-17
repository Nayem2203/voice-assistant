import os
import io
import base64
from flask import Flask, request, send_file, jsonify
# 🟢 Note the updated imports for types
from google import genai
from google.genai import types 
from gtts import gTTS

# Setup Client
MY_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=MY_API_KEY)

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        print("Gemini is listening...")
        # 🟢 FIX: Use types.Part.from_bytes to satisfy Pydantic validation
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Respond briefly as a helpful assistant in under 30 words.",
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type='audio/wav'
                )
            ]
        )
        
        bot_text = response.text
        print(f"Response: {bot_text}")

        # Voice Generation in RAM
        tts = gTTS(text=bot_text, lang='en')
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
        # Print the full error to Render logs so we can see it
        print(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)