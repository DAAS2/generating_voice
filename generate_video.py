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