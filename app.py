import os
import time
# 🟢 Note the different import for the 2026 SDK
from google import genai 
from flask import Flask, request, send_file, jsonify
from gtts import gTTS

# 1. New Client Setup
MY_API_KEY = "AQ.Ab8RN6JaAIFCGiTl81c7ph-LHn6ch3mvRRr8HbtyMeUaDL2gDA"
client = genai.Client(api_key=MY_API_KEY)

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_voice():
    try:
        audio_file = request.files['audio']
        audio_path = "temp_audio.wav"
        audio_file.save(audio_path)

        # 2. Upload using the Client
        print("Uploading to Gemini...")
        # In the new SDK, we use client.files.upload
        uploaded_file = client.files.upload(file=audio_path)

        print("Gemini is thinking...")
        # 3. Generate Content
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
        tts.save("response.mp3")

        return send_file("response.mp3", mimetype="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)