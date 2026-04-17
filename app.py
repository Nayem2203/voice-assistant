import os
import time
from google import genai 
from flask import Flask, request, send_file, jsonify
from gtts import gTTS

# 1. New Client Setup - pulling from Render environment variables
# Note: Ensure you named it GEMINI_API_KEY in the Render dashboard!
MY_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=MY_API_KEY)

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file found"}), 400

        audio_file = request.files['audio']
        audio_path = "temp_audio.wav"
        audio_file.save(audio_path)

        # 2. Upload using the Client
        print("Uploading to Gemini...")
        uploaded_file = client.files.upload(file=audio_path)

        print("Gemini is thinking...")
        # 3. Generate Content
        # We use gemini-1.5-flash for maximum stability on free tiers
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "Listen to this audio and respond as a helpful assistant. Keep it under 50 words.",
                uploaded_file
            ]
        )
        
        bot_text = response.text
        print(f"Bot response: {bot_text}")

        # 4. Voice Generation
        tts = gTTS(text=bot_text, lang='en')
        output_path = "response.mp3"
        tts.save(output_path)

        # Cleanup Gemini file on their server (keeps your project clean)
        client.files.delete(name=uploaded_file.name)

        return send_file(output_path, mimetype="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render requires the app to bind to the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)