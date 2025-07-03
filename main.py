from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
from google import generativeai as genai
from generate_video import generate_video
from create_raw_voices import generate_viral_conversation, create_ai_voices
import time
from duplicate_audio import duplicate_audio
import random
from moviepy import VideoFileClip

app = Flask(__name__)

# Configure Gemini API
GOOGLE_API_KEY = "AIzaSyCjziDNkVf-xuzSdMFMYPGtkS8CeGv3qC4"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Ensure required directories exist
os.makedirs("downloads", exist_ok=True)
os.makedirs("audios", exist_ok=True)
os.makedirs("static/generated", exist_ok=True)

@app.route('/')
def index():
    voices = [f for f in os.listdir("audios") if f.endswith(('.wav', '.mp3'))]
    backdrops = [f for f in os.listdir("downloads") if f.endswith(('.mp4', '.avi', '.mov'))]
    return render_template('index.html', voices=voices, backdrops=backdrops)

@app.route('/generate-prompt', methods=['POST'])
def generate_prompt():
    try:
        data = request.json
        topic = data.get('topic')
        style = data.get('style', 'conversational')
        length = data.get('length', 'medium')
        
        # Use generate_viral_conversation from create_raw_voices.py
        script = generate_viral_conversation()
        if not script:
            raise Exception("Failed to generate conversation")
        
        return jsonify({
            'success': True,
            'prompt': script
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        prompt = data.get('prompt')
        voice = data.get('voice')
        backdrop = data.get('backdrop')
        
        if not all([prompt, voice, backdrop]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Save the prompt to a temporary file (fix Unicode error)
        with open('temp_script.txt', 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        # Generate the cloned audio (no need to swap reference audio)
        audio_file = duplicate_audio(prompt)
        
        if not audio_file:
            return jsonify({'error': 'Audio generation failed'}), 500
        
        # Generate the video
        today_str = time.strftime('%Y-%m-%d')
        date_dir = f"static/generated/{today_str}"
        os.makedirs(date_dir, exist_ok=True)
        output_filename = f"video_{int(time.time())}.mp4"
        output_path = f"{date_dir}/{output_filename}"
        
        generate_video(
            video_path=f"downloads/{backdrop}",
            output_video=output_path,
            script=prompt,
            audio_path=audio_file
        )
        
        # Return the URL to the generated video
        video_url = f"/{output_path}"
        return jsonify({
            'success': True,
            'video_url': video_url
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-batch', methods=['POST'])
def generate_batch():
    try:
        data = request.json
        count = int(data.get('count', 10))
        voice = data.get('voice')
        backdrop = data.get('backdrop')
        
        if not all([voice, backdrop]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Prepare batch output directory
        today_str = time.strftime('%Y-%m-%d')
        date_dir = f"static/generated/{today_str}"
        os.makedirs(date_dir, exist_ok=True)
        batch_id = int(time.time())
        batch_dir = f"{date_dir}/batch_{batch_id}"
        os.makedirs(batch_dir, exist_ok=True)
        
        # Use a random script for each video, but the same audio
        # Generate the cloned audio ONCE (no need to swap reference audio)
        prompt = data.get('prompt')
        if not prompt:
            prompt = generate_viral_conversation()
        audio_file = duplicate_audio(prompt)
        
        if not audio_file:
            return jsonify({'error': 'Audio generation failed'}), 500
        
        # Get video duration
        video_path = f"downloads/{backdrop}"
        with VideoFileClip(video_path) as full_video:
            video_duration = full_video.duration
        
        video_urls = []
        for i in range(count):
            # Randomize start and end for the video clip
            clip_length = 32  # seconds (as in generate_video)
            if video_duration > clip_length:
                start = random.uniform(0, video_duration - clip_length)
                end = start + clip_length
            else:
                start = 0
                end = video_duration
            
            # Generate a new script for each video
            script = generate_viral_conversation()
            output_filename = f"video_{batch_id}_{i+1}.mp4"
            output_path = f"{batch_dir}/{output_filename}"
            
            generate_video(
                video_path=video_path,
                output_video=output_path,
                script=script,
                audio_path=audio_file,
                clip_start=start,
                clip_end=end
            )
            video_urls.append(f"/{output_path}")
        
        return jsonify({
            'success': True,
            'video_urls': video_urls,
            'batch_dir': batch_dir
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/voices')
def get_voices():
    voices = [f for f in os.listdir("audios") if f.endswith(('.wav', '.mp3'))]
    return jsonify(voices)

@app.route('/backdrops')
def get_backdrops():
    backdrops = [f for f in os.listdir("downloads") if f.endswith(('.mp4', '.avi', '.mov'))]
    return jsonify(backdrops)

# Serve audio files
@app.route('/audios/<path:filename>')
def serve_audio(filename):
    return send_from_directory('audios', filename)

# Serve video files
@app.route('/downloads/<path:filename>')
def serve_video(filename):
    return send_from_directory('downloads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)