# streamlit_app.py

import streamlit as st
import os
os.environ["COQUI_LICENSE"] = "non-commercial"
import google.generativeai as genai
import time
import random
import logging

# Configure logging for Streamlit app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- External Module Imports ---
# These are your custom Python files. Ensure they are in the same directory
# as this streamlit_app.py when you deploy.
# If they are not found or fail to import, placeholder functions will be used.
try:
    from generate_video import generate_video
    # Specifically import generate_viral_conversation and create_ai_voices from your file
    from create_raw_voices import generate_viral_conversation, create_ai_voices
    from duplicate_audio import duplicate_audio
    from moviepy import VideoFileClip
    logger.info("Successfully imported custom modules (generate_video, create_raw_voices, duplicate_audio, moviepy).")
except ImportError as e:
    logger.error(f"Failed to import a custom module: {e}. Using placeholder functions.")
    
    # Define placeholder functions if real modules are not found
    def generate_video(video_path, output_video, script, audio_path, clip_start=0, clip_end=None):
        logger.warning(f"PLACEHOLDER: generate_video called. Outputting dummy file: {output_video}")
        os.makedirs(os.path.dirname(output_video) or '.', exist_ok=True)
        with open(output_video, 'w') as f:
            f.write(f"Dummy video generated for script: '{script}' with audio from '{audio_path}' and backdrop '{video_path}'")
        return True # Simulate success

    # Placeholder for generate_viral_conversation (NO LLM CALL HERE - that's in user's actual file)
    def generate_viral_conversation(topic=None, style=None, length=None): # Note: original function takes no args
        logger.warning("PLACEHOLDER: generate_viral_conversation called. Returning dummy script.")
        # We don't perform LLM call here because the user's actual file handles it.
        return f"This is a dummy viral conversation script for {topic}."

    def create_ai_voices(script, output_file="audios/final_output.mp3", reference_audio=None):
        logger.warning("PLACEHOLDER: create_ai_voices called. Simulating audio creation.")
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(f"Dummy audio content for script: {script}")
        return output_file, None # Simulate success, no timings

    def duplicate_audio(prompt_text):
        logger.warning(f"PLACEHOLDER: duplicate_audio called for prompt: '{prompt_text}'. Returning dummy audio path.")
        dummy_audio_path = os.path.join("audios", f"dummy_audio_{int(time.time())}.mp3")
        os.makedirs("audios", exist_ok=True) # Ensure audios dir exists for dummy
        with open(dummy_audio_path, 'w') as f:
            f.write(f"Dummy audio content for: {prompt_text}")
        return dummy_audio_path

    VideoFileClip = None # Cannot mock this for proper functionality; warn if used.
    logger.warning("MoviePy's VideoFileClip is not available. Video duration functions may not work.")


# --- Configuration ---
# Streamlit provides a secure way to handle secrets via st.secrets
# For local development, you can put secrets in .streamlit/secrets.toml
# For deployment, configure them in your hosting environment (e.g., Azure App Service Application Settings)
    

try:
    genai.configure(api_key="AIzaSyCjziDNkVf-xuzSdMFMYPGtkS8CeGv3qC4")
    model = genai.GenerativeModel('gemini-2.0-flash')
    logger.info("Gemini API configured successfully in streamlit_app.py.")
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}. Please check your API key.")
    logger.exception("Error configuring Gemini API:")
    model = None # Ensure model is None if configuration fails

# --- Directory Setup ---
# These directories are local to the Streamlit app's container/machine.
# For persistent storage on Azure, consider Azure Blob Storage.
DOWNLOADS_DIR = "downloads"
AUDIOS_DIR = "audios"
GENERATED_DIR = "static/generated"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(AUDIOS_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
logger.info(f"Ensured directories exist: {DOWNLOADS_DIR}, {AUDIOS_DIR}, {GENERATED_DIR}")

# --- Utility Functions (Adapted from Flask app for Streamlit) ---

@st.cache_data # Cache results of this function to avoid re-running on every interaction
def get_voices():
    """Lists available voice audio files from the audios directory."""
    if not os.path.exists(AUDIOS_DIR):
        return []
    voices = [f for f in os.listdir(AUDIOS_DIR) if f.endswith(('.wav', '.mp3'))]
    logger.info(f"Found {len(voices)} voices in {AUDIOS_DIR}.")
    return voices

@st.cache_data # Cache results of this function
def get_backdrops():
    """Lists available video backdrop files from the downloads directory."""
    if not os.path.exists(DOWNLOADS_DIR):
        return []
    backdrops = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith(('.mp4', '.avi', '.mov'))]
    logger.info(f"Found {len(backdrops)} backdrops in {DOWNLOADS_DIR}.")
    return backdrops

# --- Streamlit UI Layout ---

st.set_page_config(layout="wide", page_title="AI Video Generator")

st.title("🎬 AI-Powered Video Generator")
st.markdown("Generate engaging videos by combining AI-generated scripts, voice cloning, and custom backdrops.")

# --- Tabbed Interface for different functionalities ---
tab1, tab2, tab3 = st.tabs(["Generate Prompt", "Generate Single Video", "Generate Batch Videos"])

# --- Tab 1: Generate Prompt ---
with tab1:
    st.header("✍️ Generate Conversation Prompt")

    st.info("Note: This feature relies on `generate_viral_conversation()` from your `create_raw_voices.py` module. Ensure that file is present and correctly uses the Gemini API.")

    topic = st.text_input("Topic for Conversation:", "latest tech trends")
    style = st.selectbox("Conversation Style:", ["conversational", "humorous", "educational", "dramatic"], index=0)
    length = st.selectbox("Conversation Length:", ["short", "medium", "long"], index=1)

    if st.button("Generate Script"):
        if model is None:
            st.warning("Gemini API not configured in `streamlit_app.py`. Check your secrets.")
        else:
            with st.spinner("Generating script..."):
                try:
                    script = ""
                    # Use the imported generate_viral_conversation directly, which now handles LLM call
                    # The imported function from create_raw_voices.py takes no arguments.
                    if 'generate_viral_conversation' in locals() and callable(generate_viral_conversation):
                        script = generate_viral_conversation()
                        logger.info("Called generate_viral_conversation from create_raw_voices.py.")
                    else:
                        # Fallback to simple placeholder if import failed
                        script = f"Fallback placeholder script for topic: {topic}."
                        logger.warning("Using simple placeholder as generate_viral_conversation from create_raw_voices.py failed to import.")
                    
                    if not script:
                        st.error("Failed to generate script. The generative model might have returned an empty response or an error occurred in `generate_viral_conversation`.")
                    else:
                        st.subheader("Generated Script:")
                        st.text_area("Review and Edit Script", script, height=200)
                        st.session_state.current_prompt = script # Store for later use
                except Exception as e:
                    logger.exception("Error generating prompt:")
                    st.error(f"An error occurred while generating the script: {e}")

# --- Tab 2: Generate Single Video ---
with tab2:
    st.header("🎥 Generate Single Video")

    voices = get_voices()
    backdrops = get_backdrops()

    if not voices:
        st.warning(f"No voice audio files found in '{AUDIOS_DIR}'. Please upload `.wav` or `.mp3` files.")
    if not backdrops:
        st.warning(f"No video backdrop files found in '{DOWNLOADS_DIR}'. Please upload `.mp4`, `.avi`, or `.mov` files.")

    selected_voice = st.selectbox("Select Voice", voices, key="single_voice_select")
    selected_backdrop = st.selectbox("Select Video Backdrop", backdrops, key="single_backdrop_select")

    # Pre-fill prompt from session state if generated
    default_prompt = st.session_state.get('current_prompt', "")
    video_prompt = st.text_area("Video Script:", value=default_prompt, height=200, key="single_video_prompt")

    if st.button("Generate Video", key="generate_single_btn"):
        if not video_prompt or not selected_voice or not selected_backdrop:
            st.error("Please fill in all required fields.")
        else:
            with st.spinner("Generating video... This might take a while."):
                try:
                    # Save the prompt to a temporary file (as in original Flask app)
                    temp_script_path = 'temp_script.txt'
                    with open(temp_script_path, 'w') as f:
                        f.write(video_prompt)
                    logger.info(f"Prompt saved to {temp_script_path}")

                    # Duplicate the audio using the selected voice
                    # Original logic involves renaming, which is risky in concurrent/serverless envs.
                    # Ideally, duplicate_audio takes the voice path directly.
                    audio_file = None
                    if 'duplicate_audio' in locals() and callable(duplicate_audio):
                        reference_audio_path = os.path.join(AUDIOS_DIR, selected_voice)
                        temp_reference = os.path.join(AUDIOS_DIR, "final_output.wav")
                        backup_reference = None

                        if not os.path.exists(reference_audio_path):
                            st.error(f"Selected voice file not found: {reference_audio_path}")
                            raise FileNotFoundError("Voice file missing")

                        try:
                            if os.path.exists(temp_reference):
                                backup_reference = temp_reference + ".bak"
                                os.rename(temp_reference, backup_reference)
                            os.rename(reference_audio_path, temp_reference)
                            
                            audio_file = duplicate_audio(video_prompt) # Assuming it uses temp_reference internally
                        finally:
                            if os.path.exists(temp_reference):
                                os.rename(temp_reference, reference_audio_path)
                            if backup_reference and os.path.exists(backup_reference):
                                os.rename(backup_reference, temp_reference)
                    else:
                        audio_file = duplicate_audio(video_prompt) # Use placeholder if no module

                    if not audio_file or not os.path.exists(audio_file):
                        st.error("Audio generation failed or audio file not found.")
                        raise Exception("Audio generation failed")

                    output_filename = f"video_{int(time.time())}.mp4"
                    output_path = os.path.join(GENERATED_DIR, output_filename)
                    
                    video_backdrop_path = os.path.join(DOWNLOADS_DIR, selected_backdrop)
                    if not os.path.exists(video_backdrop_path):
                        st.error(f"Selected backdrop file not found: {video_backdrop_path}")
                        raise FileNotFoundError("Backdrop file missing")

                    if 'generate_video' in locals() and callable(generate_video):
                        generate_video(
                            video_path=video_backdrop_path,
                            output_video=output_path,
                            script=video_prompt,
                            audio_path=audio_file
                        )
                    else:
                        generate_video(video_backdrop_path, output_path, video_prompt, audio_file) # Calls placeholder

                    if os.path.exists(output_path):
                        st.success("Video generated successfully!")
                        st.video(output_path, format="video/mp4", start_time=0)
                        # Option to download
                        with open(output_path, "rb") as file:
                            st.download_button(
                                label="Download Video",
                                data=file,
                                file_name=output_filename,
                                mime="video/mp4"
                            )
                    else:
                        st.error("Video file was not created successfully.")

                except FileNotFoundError as fnfe:
                    st.error(f"Required file not found: {fnfe}")
                    logger.exception("File Not Found Error during single video generation:")
                except Exception as e:
                    logger.exception("Error during single video generation:")
                    st.error(f"An error occurred during video generation: {e}")

# --- Tab 3: Generate Batch Videos ---
with tab3:
    st.header("Multiple Video Batch Generation")

    voices = get_voices()
    backdrops = get_backdrops()

    batch_voice = st.selectbox("Select Voice for Batch", voices, key="batch_voice_select")
    batch_backdrop = st.selectbox("Select Video Backdrop for Batch", backdrops, key="batch_backdrop_select")
    batch_count = st.number_input("Number of Videos to Generate (Max 5 for demo):", min_value=1, max_value=5, value=1) # Limiting for demo

    st.info("Each video in the batch will have a new generated script (placeholder if module not available) but use the same voice and backdrop.")

    if st.button("Generate Batch Videos", key="generate_batch_btn"):
        if not batch_voice or not batch_backdrop:
            st.error("Please select a voice and backdrop for batch generation.")
        else:
            with st.spinner(f"Generating {batch_count} videos in batch... This will take a while."):
                try:
                    batch_id = int(time.time())
                    batch_dir = os.path.join(GENERATED_DIR, f"batch_{batch_id}")
                    os.makedirs(batch_dir, exist_ok=True)
                    logger.info(f"Created batch output directory: {batch_dir}")

                    # Prepare audio (use the selected voice, only once for the batch)
                    audio_file = None
                    if 'duplicate_audio' in locals() and callable(duplicate_audio):
                        prompt_for_audio = "Dummy prompt for batch audio generation." # Original was data.get('prompt')
                        # Use the imported generate_viral_conversation for batch audio prompt
                        if 'generate_viral_conversation' in locals() and callable(generate_viral_conversation):
                             prompt_for_audio = generate_viral_conversation()
                             logger.info("Generated prompt for batch audio using generate_viral_conversation from create_raw_voices.py.")
                        else:
                             prompt_for_audio = "Fallback dummy prompt for batch audio."
                             logger.warning("Using fallback dummy prompt for batch audio as generate_viral_conversation from create_raw_voices.py failed to import.")


                        reference_audio_path = os.path.join(AUDIOS_DIR, batch_voice)
                        temp_reference = os.path.join(AUDIOS_DIR, "final_output.wav")
                        backup_reference = None

                        if not os.path.exists(reference_audio_path):
                            st.error(f"Selected voice file not found for batch: {reference_audio_path}")
                            raise FileNotFoundError("Batch voice file missing")

                        try:
                            if os.path.exists(temp_reference):
                                backup_reference = temp_reference + ".bak"
                                os.rename(temp_reference, backup_reference)
                            os.rename(reference_audio_path, temp_reference)
                            
                            audio_file = duplicate_audio(prompt_for_audio)
                        finally:
                            if os.path.exists(temp_reference):
                                os.rename(temp_reference, reference_audio_path)
                            if backup_reference and os.path.exists(backup_reference):
                                os.rename(backup_reference, temp_reference)
                    else:
                        audio_file = duplicate_audio("Batch audio prompt") # Use placeholder

                    if not audio_file or not os.path.exists(audio_file):
                        st.error("Batch audio generation failed or audio file not found.")
                        raise Exception("Batch audio generation failed")

                    video_backdrop_path = os.path.join(DOWNLOADS_DIR, batch_backdrop)
                    if not os.path.exists(video_backdrop_path):
                        st.error(f"Selected backdrop file not found for batch: {video_backdrop_path}")
                        raise FileNotFoundError("Batch backdrop file missing")

                    video_duration = 0
                    if VideoFileClip:
                        try:
                            with VideoFileClip(video_backdrop_path) as full_video:
                                video_duration = full_video.duration
                        except Exception as clip_e:
                            logger.error(f"Error getting video clip duration for {video_backdrop_path}: {clip_e}")
                            st.warning("Could not get backdrop video duration. Using full length for clips.")
                    else:
                        st.warning("MoviePy's VideoFileClip not available for batch. Cannot get video duration.")

                    video_urls = []
                    for i in range(batch_count):
                        clip_length = 32  # seconds (as in original Flask app)
                        start = 0
                        end = video_duration # Default to full video if duration couldn't be determined or is too short

                        if video_duration > clip_length:
                            start = random.uniform(0, video_duration - clip_length)
                            end = start + clip_length
                        
                        # Generate a new script for each video in the batch
                        script = ""
                        # Use the imported generate_viral_conversation for each batch video script
                        if 'generate_viral_conversation' in locals() and callable(generate_viral_conversation):
                             script = generate_viral_conversation()
                             logger.info(f"Generated script for batch video {i+1} using generate_viral_conversation from create_raw_voices.py.")
                        else:
                             script = f"Fallback dummy script for batch video {i+1}."
                             logger.warning(f"Using fallback dummy script for batch video {i+1} as generate_viral_conversation from create_raw_voices.py failed to import.")


                        output_filename = f"video_{batch_id}_{i+1}.mp4"
                        output_path = os.path.join(batch_dir, output_filename)
                        
                        if 'generate_video' in locals() and callable(generate_video):
                            generate_video(
                                video_path=video_backdrop_path,
                                output_video=output_path,
                                script=script,
                                audio_path=audio_file,
                                clip_start=start,
                                clip_end=end
                            )
                        else:
                            generate_video(video_backdrop_path, output_path, script, audio_file) # Calls placeholder

                        if os.path.exists(output_path):
                            video_urls.append(output_path)
                        else:
                            logger.error(f"Batch video {i+1} was not created at {output_path}")
                            st.warning(f"Batch video {i+1} failed to generate.")

                    if video_urls:
                        st.success(f"Generated {len(video_urls)} videos in batch!")
                        for url in video_urls:
                            st.subheader(f"Generated Video: {os.path.basename(url)}")
                            st.video(url, format="video/mp4", start_time=0)
                            with open(url, "rb") as file:
                                st.download_button(
                                    label=f"Download {os.path.basename(url)}",
                                    data=file,
                                    file_name=os.path.basename(url),
                                    mime="video/mp4",
                                    key=f"download_{os.path.basename(url)}" # Unique key
                                )
                    else:
                        st.error("No videos were generated in the batch.")

                except FileNotFoundError as fnfe:
                    st.error(f"Required file not found: {fnfe}")
                    logger.exception("File Not Found Error during batch video generation:")
                except Exception as e:
                    logger.exception("Error during batch video generation:")
                    st.error(f"An error occurred during batch video generation: {e}")