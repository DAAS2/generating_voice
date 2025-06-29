from moviepy import *
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import numpy as np
import whisper 
import os
import json
import speech_recognition as sr
from datetime import timedelta

# --- 1. Load files ---
# Load the full video clip and resize for better performance
full_video = VideoFileClip("downloads/subway_surfer.mp4")
video = full_video.subclipped(10, 42)

# Load audio clips with fallback options
def load_audio_file(filename, fallback_filename=None):
    try:
        return AudioFileClip(filename)
    except FileNotFoundError:
        if fallback_filename and os.path.exists(fallback_filename):
            print(f"Warning: {filename} not found, using {fallback_filename} instead")
            return AudioFileClip(fallback_filename)
        else:
            print(f"Warning: {filename} not found, using video's original audio")
            return None

# Load both audio clips with fallbacks
raw_audio = load_audio_file("audios/final_output.mp3", "audios/final_output.wav")
clone_audio = load_audio_file("audios/final_output.wav", "audios/final_output.mp3")

# Determine the final duration
durations = [video.duration]
if raw_audio:
    durations.append(raw_audio.duration)
if clone_audio:
    durations.append(clone_audio.duration)
final_duration = min(durations)

# Trim video and audio to final_duration
video = video.subclipped(0, final_duration)
if raw_audio:
    raw_audio = raw_audio.subclipped(0, final_duration)
if clone_audio:
    clone_audio = clone_audio.subclipped(0, final_duration)

# Set the audio to the trimmed video clip
if clone_audio:
    video = video.with_audio(clone_audio)
elif raw_audio:
    video = video.with_audio(raw_audio)
# If no audio is available, video will keep its original audio

# --- 2. Prepare script (split into words) ---
full_script_lines = """
[Boy] Bro you won't believe what happened at the gym
[Girl] Spill the tea bestie
[Boy] This dude was flexing hard in the mirror no cap
[Girl] Standard gym behaviour bruh
[Boy] But he was flexing his teeth
[Girl] Wait what SFX laugh
[Boy] Dead serious He even winked at himself
[Girl] That's my dad He's been practicing for his dentures
""".strip().split('\n')

# --- 3. Load word timings from raw audio ---
def load_word_timings():
    try:
        with open("word_timings.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Word timings file not found. Using Whisper transcription...")
        return None

# --- 4. Audio analysis with multiple methods ---
def get_word_timestamps():
    # First try to load pre-generated word timings
    word_timings = load_word_timings()
    if word_timings:
        return word_timings

    # If no pre-generated timings, use Whisper
    transcription_cache_file = "transcription_cache.json"
    
    if os.path.exists(transcription_cache_file):
        print("Loading cached transcription...")
        with open(transcription_cache_file, 'r') as f:
            whisper_transcription = json.load(f)
    else:
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Transcribing audio with word timestamps...")
        # Try to use raw audio first, fall back to clone audio if needed
        audio_file = "audios/final_output.mp3" if os.path.exists("audios/final_output.mp3") else "audios/final_output.wav"
        whisper_transcription = model.transcribe(audio_file, word_timestamps=True, fp16=False)
        with open(transcription_cache_file, 'w') as f:
            json.dump(whisper_transcription, f)
    
    # Create a list of all words with their timestamps
    word_timestamps = []
    for segment in whisper_transcription['segments']:
        for word_info in segment['words']:
            word = word_info['word'].strip().lower().rstrip('.,!?')
            if word:
                word_timestamps.append({
                    'word': word,
                    'start': word_info['start'],
                    'end': word_info['end']
                })
    
    return word_timestamps

# Get all word timestamps
all_word_timestamps = get_word_timestamps()

def find_word_timing(word, current_time, all_timestamps):
    word = word.lower().strip('.,!?')
    
    # Try to find exact match
    for timestamp in all_timestamps:
        if timestamp['word'] == word:
            return timestamp['start'], timestamp['end']
    
    # If no exact match, find surrounding words
    surrounding_timestamps = []
    for i, timestamp in enumerate(all_timestamps):
        if abs(timestamp['start'] - current_time) < 2.0:  # Look within 2 seconds
            surrounding_timestamps.append(timestamp)
    
    if surrounding_timestamps:
        # Calculate average word duration from surrounding words
        avg_duration = sum(t['end'] - t['start'] for t in surrounding_timestamps) / len(surrounding_timestamps)
        # Use the closest timestamp as reference
        closest = min(surrounding_timestamps, key=lambda x: abs(x['start'] - current_time))
        return closest['start'], closest['start'] + avg_duration
    
    return None

# --- 5. Generate Text Clips with Effects ---
text_clips = []

# Styling constants
HIGHLIGHT_FONT_SIZE = 32
BOY_COLOR = '#FFFFFF'
GIRL_COLOR = '#FFFFFF'
STROKE_COLOR = 'black'
STROKE_WIDTH = 3
TEXT_POSITION = ('center', 'center')
FONT = 'fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf'

# Create progress bar
progress_bar = (ColorClip(size=(int(video.w), 8), color=(255, 255, 255))
    .with_opacity(0.7)
    .with_duration(final_duration)
    .with_position(('center', 10)))

def create_text_clip(text, start_time, duration):
    return (TextClip(
        text=text,
        font_size=HIGHLIGHT_FONT_SIZE,
        color=BOY_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=STROKE_WIDTH,
        method='caption',
        size=(300, 300),
        font=FONT
    )
    .with_start(start_time)
    .with_duration(duration)
    .with_position(TEXT_POSITION))

# Process each line
current_time = 0
MIN_WORD_DURATION = 0.3
MAX_WORD_DURATION = 1.0
LINE_BREAK_DURATION = 0.5

for line_text in full_script_lines:
    # Extract speaker and content
    if line_text.startswith('['):
        speaker_end = line_text.find(']') + 1
        speaker = line_text[:speaker_end]
        content = line_text[speaker_end:].strip()
        is_boy = '[Boy]' in speaker
    else:
        speaker = ""
        content = line_text
        is_boy = True

    # Add speaker marker if present
    if speaker:
        speaker_clip = create_text_clip(speaker, current_time, MIN_WORD_DURATION)
        text_clips.append(speaker_clip)
        current_time += MIN_WORD_DURATION

    # Process content words
    words = content.split()
    
    # First pass: find timing for all words
    word_timings = []
    for word in words:
        timing = find_word_timing(word, current_time, all_word_timestamps)
        if timing:
            start, end = timing
            word_timings.append((word, start, end))
            current_time = end  # Update current time to the end of this word
        else:
            # If no timing found, use current time with minimum duration
            word_timings.append((word, current_time, current_time + MIN_WORD_DURATION))
            current_time += MIN_WORD_DURATION

    # Second pass: create clips with exact timing
    for word, start, end in word_timings:
        duration = end - start
        duration = max(MIN_WORD_DURATION, min(duration, MAX_WORD_DURATION))
        
        # Create the text clip
        word_clip = create_text_clip(word, start, duration)
        text_clips.append(word_clip)

    # Add line break timing
    current_time += LINE_BREAK_DURATION

# --- 6. Compose final video ---
final_clips = [video, progress_bar] + text_clips
final = CompositeVideoClip(final_clips, size=video.size)
final = final.with_duration(final_duration)

# Use high-quality encoding settings
final.write_videofile(
    "WavaAI_Video.mp4",
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

print("Video with WavaAI style text generated successfully!")