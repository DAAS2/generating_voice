import os
import streamlit as st
import builtins

_real_input = builtins.input

def patched_input(prompt=""):
    # Use a distinctive, unique part of the prompt
    if "Otherwise, I agree to the terms of the non-commercial CPML" in prompt:
        return "y"
    return _real_input(prompt)

builtins.input = patched_input
os.environ["COQUI_LICENSE"] = "non-commercial"

from TTS.api import TTS
import soundfile as sf  # For reliable audio saving
import noisereduce as nr  # Optional
import librosa  # For audio loading and resampling
import re
import torch

# --- SETUP ---
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Starting duplicate_audio.py - Using device: {device}")

# --- LIGHTWEIGHT AUDIO PREPROCESSING ---
def preprocess_audio(input_path, output_path):
    try:
        # Load audio (keep original sample rate unless >44.1kHz)
        y, sr = librosa.load(input_path, sr=None)
        if sr > 44100:
            y = librosa.resample(y, orig_sr=sr, target_sr=44100)
            sr = 44100
        
        # Only apply noise reduction if background noise exists
        if len(y) > 0:
            y = nr.reduce_noise(y=y, sr=sr, stationary=True, prop_decrease=0.5)  # Mild reduction
        
        # Normalize without over-driving
        y = y * (0.9 / max(0.01, max(abs(y))))  # Safer than librosa.util.normalize
        
        sf.write(output_path, y, sr)
        return output_path
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        return input_path  # Fallback to original

# --- INIT TTS WITH OPTIMIZED PARAMS ---
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

def duplicate_audio(text):
    """Duplicate audio based on the given text, removing speaker tags like [Boy] and [Girl]"""
    try:
        # Remove speaker tags (e.g., [Boy], [Girl]) from each line
        cleaned_lines = []
        for line in text.splitlines():
            cleaned_line = re.sub(r"^\s*\[.*?\]\s*", "", line)
            if cleaned_line.strip():
                cleaned_lines.append(cleaned_line.strip())
        cleaned_text = " ".join(cleaned_lines)
        
        # Ensure audios directory exists
        os.makedirs("audios", exist_ok=True)
        
        # 1. Preprocess reference audio (skip if it causes issues)
        ref_audio = "audios/final_output.wav"  # Use the original voice
        processed_audio = "audios/processed_reference.wav"
        processed_audio = preprocess_audio(ref_audio, processed_audio)
        
        # 2. Generate raw output
        output_raw = "audios/raw_output.wav"
        tts.tts_to_file(
            text=cleaned_text,  # Cleaned text without speaker tags
            speaker_wav=processed_audio,
            language="en",
            file_path=output_raw,
            speed=1.1,  # Avoid speed modifications (can cause artifacts)
            temperature=0.6,  # Lower = more stable
            length_penalty=1.0,  # Prevents cut-offs
            split_sentences=True,
        )
        
        # 3. Optional: Light postprocessing (only volume normalization)
        y, sr = librosa.load(output_raw, sr=None)
        y = y * (0.9 / max(abs(y)))  # Simple peak normalization
        output_file = "audios/final_output_clone.wav"
        sf.write(output_file, y, sr)
        print("Done! Output saved to audios/final_output_clone.wav")
        return output_file
    except Exception as e:
        print(f"Voice duplication failed: {e}")
        return None
