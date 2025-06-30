from google import generativeai as genai
from gtts import gTTS
import subprocess
import re
import os
import time
import json
import numpy as np


# Initialize Gemini (correct API)
genai.configure(api_key="AIzaSyCjziDNkVf-xuzSdMFMYPGtkS8CeGv3qC4")

# Voice settings for realistic female voice (Jessica-like)
VOICE_SETTINGS = {
    "Girl": {
        "tld": "co.uk",  # British English for more natural tone
        "effects": [
            "atempo=1.05",  # Slightly faster for natural flow
            "equalizer=f=1000:width_type=h:width=200:g=-2",  # Reduce harshness
            "equalizer=f=2000:width_type=h:width=300:g=2",  # Enhance clarity
            "equalizer=f=5000:width_type=h:width=400:g=-3",  # Reduce sibilance
            "highpass=f=100",  # Remove low rumble
            "lowpass=f=8000",  # Remove high noise
            "compand=attacks=0.05:decays=0.1:points=-80/-80|-60/-60|-40/-40|-20/-20|0/0",  # Dynamic range compression
            "volume=1.2"  # Slightly increase volume
        ]
    }
}

def get_audio_duration(file_path):
    """Get duration of an audio file using ffprobe"""
    cmd = [
        'ffprobe', 
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def adjust_audio_speed(input_file, output_file, target_duration):
    """Adjust audio speed to match target duration"""
    current_duration = get_audio_duration(input_file)
    speed_factor = current_duration / target_duration
    
    subprocess.run([
        'ffmpeg',
        '-i', input_file,
        '-filter:a', f'atempo={speed_factor}',
        '-y', output_file
    ], check=True)

def create_ai_voices(script, output_file="audios/final_output.mp3", reference_audio=None):
    temp_files = []
    temp_dir = "temp_audio"
    word_timings = []  # Store word timings
    current_time = 0
    
    try:
        os.makedirs(temp_dir, exist_ok=True)
        
        # If reference audio provided, get its duration
        reference_duration = None
        if reference_audio:
            reference_duration = get_audio_duration(reference_audio)
        
        # First pass: generate all audio files
        for line in [ln.strip() for ln in script.split('\n') if ln.strip()]:
            match = re.match(r'\[(.*?)\](.*)', line)
            if not match:
                print(f"Skipping malformed line: {line}")
                continue
                
            speaker, text = match.groups()
            text = text.strip()
            
            if not text:
                continue
            
            # Generate raw voice
            raw_file = os.path.join(temp_dir, f"raw_{speaker}_{hash(text)}.mp3")
            try:
                tts = gTTS(
                    text=text,
                    lang='en',
                    tld=VOICE_SETTINGS["Girl"]["tld"],
                    slow=False
                )
                tts.save(raw_file)
                
                # Process with effects
                processed_file = os.path.join(temp_dir, f"processed_{speaker}_{hash(text)}.mp3")
                subprocess.run([
                    'ffmpeg', '-i', raw_file,
                    '-af', ",".join(VOICE_SETTINGS["Girl"]["effects"]),
                    '-ar', '44100',
                    '-y', processed_file
                ], check=True)
                
                # If reference audio exists, adjust speed
                if reference_duration:
                    adjusted_file = os.path.join(temp_dir, f"adjusted_{speaker}_{hash(text)}.mp3")
                    adjust_audio_speed(processed_file, adjusted_file, reference_duration)
                    if os.path.exists(adjusted_file):
                        temp_files.append(adjusted_file)
                else:
                    if os.path.exists(processed_file):
                        temp_files.append(processed_file)
                
                # Store word timings
                words = text.split()
                word_duration = get_audio_duration(processed_file) / len(words)
                for word in words:
                    word_timings.append({
                        'word': word,
                        'start': current_time,
                        'end': current_time + word_duration
                    })
                    current_time += word_duration
                
                # Clean up raw file
                if os.path.exists(raw_file):
                    os.remove(raw_file)
                
            except Exception as e:
                print(f"Error processing audio: {e}")
                continue
            time.sleep(0.1)
        
        if not temp_files:
            print("No audio files generated!")
            return None, None
            
        # Verify all files exist before concatenation
        valid_files = [f for f in temp_files if os.path.exists(f)]
        if not valid_files:
            print("No valid audio files found for concatenation!")
            return None, None
            
        # Create a complex filter for concatenation
        inputs = []
        filter_complex = []
        
        for i in range(len(valid_files)):
            inputs.extend(['-i', valid_files[i]])
            filter_complex.append(f'[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}];')
        
        # Add concat filter
        filter_complex.append(''.join([f'[a{i}]' for i in range(len(valid_files))]) + 
                            f'concat=n={len(valid_files)}:v=0:a=1[out]')
        
        filter_complex = ''.join(filter_complex)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        subprocess.run([
            'ffmpeg',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-c:a', 'libmp3lame',
            '-b:a', '192k',
            '-ar', '44100',
            '-y', output_file
        ], check=True)
        
        # Save word timings to JSON
        timings_file = "word_timings.json"
        with open(timings_file, 'w') as f:
            json.dump(word_timings, f, indent=2)
        
        print(f"✅ High-quality audio saved to {output_file}")
        print(f"✅ Word timings saved to {timings_file}")
        return output_file, timings_file
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None
    finally:
        # Cleanup
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        try:
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass

# Generate viral conversation
def generate_viral_conversation():
    prompt = """Create a 30-second viral conversation between two people for a short video. 
        Follow these EXACT requirements:
        
        FORMAT:
        [Boy] Message text here
        [Girl] Response text here
        [Boy] Next message
        [Girl] Final punchline
        
        CONTENT RULES:
        1. Must have 6-8 rapid exchanges (2-3 seconds each)
        2. Start with an attention-grabbing hook
        3. Use modern slang and viral phrases
        4. Include 1-2 trending sounds/effects mentions (like "bruh", "wait what?", "no cap")
        5. End with a surprising twist or punchline
        7. Maximum 120 words total
        
        EXAMPLE:
        [Boy] Just found out my gf has been...
        [Girl] Cheating? 
        [Boy] Worse... she puts ketchup on pizza 
        [Girl] That's a CRIME!
        [Boy] I know right? Pineapple too!
        [Girl] Okay now you're just lying 
        
        I want it in that format instantly, don't say anything else, like here's a 30 second viral conversation, just give me the script
        """  # Your prompt here
        
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')  # Use working model
        response = model.generate_content(prompt)
        return response.text if response.text else None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    script = generate_viral_conversation()
    if script:
        print("Generated Script:\n", script)
        if audio_file := create_ai_voices(script):
            print(f"✅ Final audio: {audio_file}")
        