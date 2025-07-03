# streamlit_app.py

import streamlit as st
import os
from datetime import datetime
import zipfile
import io
import logging

# Configure logging for Streamlit app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Directory Setup ---
# Using "static/generated" as the primary video storage folder, as per your updated code.
VIDEOS_DIR = "static/generated" 

os.makedirs(VIDEOS_DIR, exist_ok=True)
logger.info(f"Ensured video directory exists: {VIDEOS_DIR}")


# --- Utility Functions ---

# Add 'persist=True' to keep the cache across reruns, but we'll clear it manually on upload.
@st.cache_data(persist=True)
def get_uploaded_videos_by_date():
    """Organizes uploaded videos by their modification date."""
    videos_by_date = {}
    if not os.path.exists(VIDEOS_DIR):
        return {}
    
    video_files = [f for f in os.listdir(VIDEOS_DIR) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))]
    
    for video_file in video_files:
        file_path = os.path.join(VIDEOS_DIR, video_file)
        try:
            # Get last modification time (useful for tracking when they were uploaded/added)
            timestamp = os.path.getmtime(file_path) # Changed to getmtime for consistency with typical file operations
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            if date not in videos_by_date:
                videos_by_date[date] = []
            videos_by_date[date].append(video_file)
        except Exception as e:
            logger.error(f"Could not get date for video {video_file}: {e}")
            
    # Sort dates in descending order (most recent first)
    sorted_dates = sorted(videos_by_date.keys(), reverse=True)
    sorted_videos_by_date = {date: sorted(videos_by_date[date]) for date in sorted_dates} # Sort videos within each date
    
    return sorted_videos_by_date

def create_zip_archive(files_to_zip, zip_filename="videos.zip"):
    """Creates a ZIP archive in-memory from a list of file paths."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for file_path in files_to_zip:
            if os.path.exists(file_path):
                zf.write(file_path, os.path.basename(file_path))
            else:
                logger.warning(f"File not found for zipping: {file_path}")
    zip_buffer.seek(0)
    return zip_buffer.getvalue(), zip_filename


# --- Streamlit UI Layout ---

st.set_page_config(layout="wide", page_title="Video Manager")

st.title("⬆️⬇️ Simple Video Uploader & Downloader")
st.markdown("Upload your video files and easily manage and download them later.")

# --- Tabbed Interface ---
tab1, tab2 = st.tabs(["Upload Videos", "Video Library"])

# --- Tab 1: Upload Videos ---
with tab1:
    st.header("📤 Upload Your Videos")
    st.markdown("Select one or more video files to upload to your library.")

    uploaded_files = st.file_uploader(
        "Choose video files", 
        type=['mp4', 'avi', 'mov', 'mkv', 'webm'], 
        accept_multiple_files=True
    )

    if uploaded_files:
        # Counter for successful uploads in this session
        successful_uploads_count = 0
        for uploaded_file in uploaded_files:
            file_path = os.path.join(VIDEOS_DIR, uploaded_file.name)
            
            # Check if file already exists to avoid overwriting or redundant messages
            if os.path.exists(file_path):
                st.info(f"File '{uploaded_file.name}' already exists. Skipping upload.")
                continue # Skip to the next file

            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Uploaded '{uploaded_file.name}' successfully!")
                logger.info(f"File uploaded: {uploaded_file.name}")
                successful_uploads_count += 1
            except Exception as e:
                st.error(f"Error uploading '{uploaded_file.name}': {e}")
                logger.error(f"Error uploading {uploaded_file.name}: {e}")
        
        # --- Crucial Fix: Clear the cache after successful uploads ---
        if successful_uploads_count > 0:
            st.cache_data.clear() # Clears the cache for all functions decorated with @st.cache_data
            st.rerun() # Rerun the app to show updated video list immediately


# --- Tab 2: Video Library ---
with tab2:
    st.header("🗄️ Your Video Library")
    st.markdown("Browse your uploaded videos, organized by date, and download them.")

    videos_by_date = get_uploaded_videos_by_date()

    if not videos_by_date:
        st.info("No videos found in your library yet. Upload some in the 'Upload Videos' tab!")
    else:
        for date, video_list in videos_by_date.items():
            # Create a more descriptive expander label
            expander_label = f"📁 Videos from {date} ({len(video_list)} videos)"
            # Use a unique key for each expander
            with st.expander(expander_label, expanded=False): # Set expanded=False to keep them collapsed initially
                
                # Option to download all videos for this day as a ZIP
                zip_files_paths = [os.path.join(VIDEOS_DIR, video) for video in video_list]
                zip_data, zip_filename = create_zip_archive(zip_files_paths, f"{date}_videos.zip")
                
                if zip_data:
                    st.download_button(
                        label=f"Download All Videos from {date} as ZIP",
                        data=zip_data,
                        file_name=zip_filename,
                        mime="application/zip",
                        key=f"download_zip_{date}" # Ensure unique key for each button
                    )
                else:
                    st.warning(f"Could not create ZIP for {date}. No files found to zip.")
                
                st.markdown("---") # Separator
                st.subheader(f"Individual Videos for {date}:")

                for video_name in video_list:
                    video_path = os.path.join(VIDEOS_DIR, video_name)
                    st.write(f"**{video_name}**")
                    
                    # Display video
                    st.video(video_path, format="video/mp4", start_time=0)
                    
                    # Individual download button
                    with open(video_path, "rb") as file:
                        st.download_button(
                            label=f"Download {video_name}",
                            data=file,
                            file_name=video_name,
                            mime="video/mp4",
                            key=f"download_single_{video_name}" # Ensure unique key for each button
                        )
                    st.markdown("---") # Separator between videos