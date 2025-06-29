from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import google.generativeai as genai
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
            
        # Save the prompt to a temporary file
        with open('temp_script.txt', 'w') as f:
            f.write(prompt)
        
        # Duplicate the audio using the selected voice
        # Temporarily swap the reference audio to the selected voice
        reference_audio_path = f"audios/{voice}"
        temp_reference = "audios/final_output.wav"
        backup_reference = None
        if os.path.exists(temp_reference):
            backup_reference = temp_reference + ".bak"
            os.rename(temp_reference, backup_reference)
        os.rename(reference_audio_path, temp_reference)
        
        # Generate the cloned audio
        audio_file = duplicate_audio(prompt)
        
        # Restore the original reference audio
        os.rename(temp_reference, reference_audio_path)
        if backup_reference:
            os.rename(backup_reference, temp_reference)
        
        if not audio_file:
            return jsonify({'error': 'Audio generation failed'}), 500
        
        # Generate the video
        output_filename = f"video_{int(time.time())}.mp4"
        output_path = f"static/generated/{output_filename}"
        
        generate_video(
            video_path=f"downloads/{backdrop}",
            output_video=output_path,
            script=prompt,
            audio_path=audio_file
        )
        
        # Return the URL to the generated video
        video_url = f"/static/generated/{output_filename}"
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
        batch_id = int(time.time())
        batch_dir = f"static/generated/batch_{batch_id}"
        os.makedirs(batch_dir, exist_ok=True)
        
        # Prepare audio (use the selected voice, only once)
        reference_audio_path = f"audios/{voice}"
        temp_reference = "audios/final_output.wav"
        backup_reference = None
        if os.path.exists(temp_reference):
            backup_reference = temp_reference + ".bak"
            os.rename(temp_reference, backup_reference)
        os.rename(reference_audio_path, temp_reference)
        
        # Use a random script for each video, but the same audio
        # Generate the cloned audio ONCE
        prompt = data.get('prompt')
        if not prompt:
            prompt = generate_viral_conversation()
        audio_file = duplicate_audio(prompt)
        
        # Restore the original reference audio
        os.rename(temp_reference, reference_audio_path)
        if backup_reference:
            os.rename(backup_reference, temp_reference)
        
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
    app.run(debug=True) 
    
    
    
    
generate_video.py

from create_raw_voices import generate_viral_conversation, create_ai_voices
from test_movie import create_text_clip
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ColorClip
import whisper
import os
import json

def get_word_timestamps_from_whisper(audio_file):
    """Get word timestamps using Whisper directly"""
    print("Loading Whisper model...")
    model = whisper.load_model("base")
    print("Transcribing audio with word timestamps...")
    transcription = model.transcribe(audio_file, word_timestamps=True, fp16=False)
    
    word_timestamps = []
    for segment in transcription['segments']:
        for word_info in segment["words"]:
            word = word_info["word"].strip().lower().rstrip('.,!?')
            if word:
                word_timestamps.append({
                    'word': word,
                    'start': word_info['start'],
                    'end': word_info['end']
                })
    return word_timestamps

def find_word_timing(word, current_time, all_timestamps, search_window=2.0):
    """Find timing for a word with improved search and interpolation"""
    word = word.lower().strip('.,!?')
    
    # Try to find exact match
    for timestamp in all_timestamps:
        if timestamp['word'] == word:
            return timestamp['start'], timestamp['end']
    
    # If no exact match, find surrounding words
    surrounding_timestamps = []
    for i, timestamp in enumerate(all_timestamps):
        if abs(timestamp['start'] - current_time) < search_window:
            surrounding_timestamps.append((i, timestamp))
    
    if surrounding_timestamps:
        # Sort by index to find words before and after
        surrounding_timestamps.sort(key=lambda x: x[0])
        
        # Find the closest timestamp before and after
        before_word = None
        after_word = None
        
        for i, timestamp in surrounding_timestamps:
            if timestamp['start'] < current_time:
                before_word = timestamp
            else:
                after_word = timestamp
                break
        
        if before_word and after_word:
            # Interpolate timing between surrounding words
            time_diff = after_word['start'] - before_word['end']
            avg_word_duration = sum(t['end'] - t['start'] for _, t in surrounding_timestamps) / len(surrounding_timestamps)
            
            # Place the word halfway between surrounding words
            start_time = before_word['end'] + (time_diff / 2)
            end_time = start_time + avg_word_duration
            
            return start_time, end_time
        elif before_word:
            # If only before word exists, add average duration
            avg_duration = sum(t['end'] - t['start'] for _, t in surrounding_timestamps) / len(surrounding_timestamps)
            return before_word['end'], before_word['end'] + avg_duration
        elif after_word:
            # If only after word exists, subtract average duration
            avg_duration = sum(t['end'] - t['start'] for _, t in surrounding_timestamps) / len(surrounding_timestamps)
            return after_word['start'] - avg_duration, after_word['start']
    
    return None

def generate_video(video_path="downloads/subway_surfer.mp4", output_video="WavaAI_Video.mp4", script=None, audio_path=None, clip_start=None, clip_end=None):

    if not script:
        script = generate_viral_conversation()

    print("Generated Script:\n", script)
    
    # 2. Use provided audio or create new voices
    if audio_path is not None:
        audio_file = audio_path
    else:
        print("\nCreating AI voices...")
        audio_file, timings_file = create_ai_voices(script)
        if not audio_file:
            print("Failed to create AI voices!")
            return
    
    # 3. Load video and prepare for text overlay
    print("\nProcessing video...")
    full_video = VideoFileClip(video_path)
    if clip_start is not None and clip_end is not None:
        video = full_video.subclipped(clip_start, clip_end)
    else:
        video = full_video.subclipped(10, 42)
    
    # Load audio clips
    raw_audio = AudioFileClip(audio_file)
    
    # Determine final duration
    final_duration = min(video.duration, raw_audio.duration)
    
    # Trim video and audio
    video = video.subclipped(0, final_duration)
    raw_audio = raw_audio.subclipped(0, final_duration)
    
    # Set audio to video
    video = video.with_audio(raw_audio)
    
    # 4. Get word timestamps using Whisper
    print("\nGetting word timestamps...")
    all_word_timestamps = get_word_timestamps_from_whisper(audio_file)
    
    # 5. Process script and create text overlays
    print("\nCreating text overlays...")
    text_clips = []
    current_time = 0
    MIN_WORD_DURATION = 0.25
    MAX_WORD_DURATION = 0.8
    LINE_BREAK_DURATION = 0.4
    WORD_GAP = 0.08
    
    # Process each line
    for line_text in script.strip().split('\n'):
        # Extract speaker and content
        if line_text.startswith('['):
            speaker_end = line_text.find(']') + 1
            content = line_text[speaker_end:].strip()
        else:
            content = line_text

        # Process content words
        words = content.split()
        
        # First pass: find timing for all words
        word_timings = []
        for i, word in enumerate(words):
            timing = find_word_timing(word, current_time, all_word_timestamps)
            if timing:
                start, end = timing
                # Ensure minimum duration and prevent overlap
                if i > 0 and word_timings:
                    prev_end = word_timings[-1][2]
                    start = max(start, prev_end + WORD_GAP)
                duration = end - start
                duration = max(MIN_WORD_DURATION, min(duration, MAX_WORD_DURATION))
                end = start + duration
                word_timings.append((word, start, end))
                current_time = end
            else:
                # If no timing found, look at surrounding words in the script
                prev_word = words[i-1] if i > 0 else None
                next_word = words[i+1] if i < len(words)-1 else None
                
                # Find timings for surrounding words
                prev_timing = find_word_timing(prev_word, current_time, all_word_timestamps) if prev_word else None
                next_timing = find_word_timing(next_word, current_time, all_word_timestamps) if next_word else None
                
                if prev_timing and next_timing:
                    # Interpolate between surrounding words
                    start = prev_timing[1] + WORD_GAP
                    end = next_timing[0] - WORD_GAP
                    # Ensure the duration isn't too long
                    duration = min(end - start, MAX_WORD_DURATION)
                    end = start + duration
                    word_timings.append((word, start, end))
                    current_time = end
                elif prev_timing:
                    # Use timing after previous word
                    start = prev_timing[1] + WORD_GAP
                    end = start + MIN_WORD_DURATION
                    word_timings.append((word, start, end))
                    current_time = end
                elif next_timing:
                    # Use timing before next word
                    end = next_timing[0] - WORD_GAP
                    start = end - MIN_WORD_DURATION
                    word_timings.append((word, start, end))
                    current_time = end
                else:
                    # No surrounding words found, use minimum duration
                    start = current_time + WORD_GAP
                    end = start + MIN_WORD_DURATION
                    word_timings.append((word, start, end))
                    current_time = end

        # Second pass: create clips with exact timing
        last_end_time = 0
        for word, start, end in word_timings:
            # Ensure no overlap with previous word and maintain minimum gap
            start = max(start, last_end_time + WORD_GAP)
            duration = end - start
            duration = max(MIN_WORD_DURATION, min(duration, MAX_WORD_DURATION))
            
            # Create the text clip
            word_clip = create_text_clip(word, start, duration)
            text_clips.append(word_clip)
            
            # Update last end time
            last_end_time = start + duration

        current_time += LINE_BREAK_DURATION

    # 6. Create progress bar
    progress_bar = (ColorClip(size=(int(video.w), 8), color=(255, 255, 255))
        .with_opacity(0.7)
        .with_duration(final_duration)
        .with_position(('center', 10)))

    # 7. Compose final video
    print("\nComposing final video...")
    final_clips = [video, progress_bar] + text_clips
    final = CompositeVideoClip(final_clips, size=video.size)
    final = final.with_duration(final_duration)

    # 8. Write final video
    print("\nWriting final video...")
    final.write_videofile(
        output_video,
        fps=60,
        codec='libx264',
        threads=8,
        preset='slow',
        bitrate='8000k',
        audio_codec='aac',
        audio_bitrate='320k',
        ffmpeg_params=[
            '-crf', '18',
            '-profile:v', 'high',
            '-level', '4.2',
            '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p'
        ]
    )

    print(f"\n✅ Video generation complete! Output saved to {output_video}")

if __name__ == "__main__":
    generate_video() 