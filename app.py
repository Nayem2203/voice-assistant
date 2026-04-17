import os
import io
import base64
from flask import Flask, request, send_file, jsonify
from google import genai
from gtts import gTTS

# 1. Setup - Pull key from Render Environment Variables
MY_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=MY_API_KEY)

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400

        # Read audio directly into memory (Fast)
        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        # 2. Prepare Inline Data (Skips the slow 'upload' step)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        print("Gemini is listening...")
        # 3. Generate Content (Using 1.5-Flash for speed/stability)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Respond briefly and helpfully in under 30 words.",
                {"mime_type": "audio/wav", "data": audio_base64}
            ]
        )
        
        bot_text = response.text
        print(f"Response: {bot_text}")

        # 4. Generate Speech in RAM (No disk write = Faster)
        tts = gTTS(text=bot_text, lang='en')
        audio_stream = io.BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)

        # Send back the MP3 stream
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
    # Binds to Render's dynamic port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)