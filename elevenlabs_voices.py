from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from google import generativeai as genai
import os

# Initialize Gemini (correct API)
genai.configure(api_key="AIzaSyCjziDNkVf-xuzSdMFMYPGtkS8CeGv3qC4")  # Replace with your actual key

load_dotenv()

elevenlabs = ElevenLabs(
    api_key="sk_233db689598b631f7066f2e0015e501deb52cc1e921ae9b9" # Replace with your actual ElevenLabs API key
)

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
        6. Add [SFX: laugh] or [SFX: gasp] where appropriate
        7. Maximum 120 words total
        
        EXAMPLE:
        [Boy] Just found out my gf has been...
        [Girl] Cheating? 😱
        [Boy] Worse... she puts ketchup on pizza 🍕
        [Girl] [SFX: gasp] That's a CRIME!
        [Boy] I know right? Pineapple too!
        [Girl] Okay now you're just lying 😤"""  # Your prompt here
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')  # Use working model
        response = model.generate_content(prompt)
        return response.text if response.text else None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def create_ai_voices(script):
    # Optimized voice settings for clarity and natural sound
    audio = elevenlabs.text_to_speech.convert(
        text=script,
        voice_id="XrExE9yKIg1WjnnlVkGX",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    # Check if audio is a generator and convert it to bytes
    if hasattr(audio, 'read'):
        audio_bytes = audio.read()
    else:
        audio_bytes = audio  # If it's already in bytes

    # Save audio bytes to an mp3 file
    with open("output.mp3", "wb") as f:
        for chunk in audio:
            f.write(chunk)

if __name__ == "__main__":
    # Example usage
    conversation = generate_viral_conversation()
    if conversation:
        print("Generated Conversation:")
        print(conversation)
        
        create_ai_voices(conversation)
        print("Audio saved as output.mp3")
    else:
        print("Failed to generate conversation.")
