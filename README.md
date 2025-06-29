🎬 AI-Powered Video Generator

This project is a Flask-based web application that leverages the Google Gemini API to generate conversational scripts, clones voices, and combines them with video backdrops to create dynamic video content. It supports single video generation and batch video generation.
✨ Features

    Prompt Generation: Generates engaging, viral conversation scripts based on a given topic, style, and length using the Google Gemini API.

    Voice Cloning/Duplication: Utilizes a selected reference audio to clone and apply a voice to the generated script.

    Video Generation: Combines the generated audio with a chosen video backdrop to produce new video content.

    Batch Generation: Capable of generating multiple videos with randomized clips from a backdrop and unique scripts, all using the same cloned voice.

    Asset Management: Manages and serves audio and video backdrop assets, as well as generated video outputs.

    RESTful API: Provides clear API endpoints for integration with a frontend.

⚙️ Prerequisites

Before you begin, ensure you have the following installed:

    Python 3.8+ (preferably 3.10-3.12 for broader library compatibility, though 3.13 is used in your logs)

    pip (Python package installer)

    ffmpeg (a command-line tool for video and audio processing, required by moviepy). Ensure it's installed and accessible in your system's PATH.

📁 Project Structure

Your project directory should be structured as follows:

.
├── app.py                      # Main Flask application
├── wsgi.py                     # WSGI entry point for production servers (like Gunicorn)
├── requirements.txt            # Python dependencies
├── create_raw_voices.py        # Module for generating viral conversations and creating AI voices
├── duplicate_audio.py          # Module for duplicating audio using a reference voice
├── generate_video.py           # Module for generating video from script, audio, and backdrop
├── audios/                     # Directory for reference audio files (e.g., voice samples)
│   └── your_voice_sample.wav
│   └── final_output.wav        # Used for temporary audio swapping
├── downloads/                  # Directory for video backdrop files
│   └── your_backdrop_video.mp4
├── static/                     # Static files (CSS, JS, images)
│   └── generated/              # Directory for generated video outputs
│       └── video_12345.mp4
│       └── batch_67890/
│           └── video_67890_1.mp4
│           └── ...
├── templates/                  # HTML templates for Flask
│   └── index.html
├── temp_script.txt             # Temporary file for storing prompts (managed by app.py)
├── final_output.mp3            # Potentially an output from voice generation (used in app.py logic)
├── test_movie.py               # (If exists) - for testing video generation
├── test.py                     # (If exists) - for general testing
├── todo.txt                    # (If exists) - project notes
├── transcription_cache.json    # (If exists) - cache for transcriptions
├── WavaAI_Video.mp4            # (If exists) - example output or source
└── word_timings.json           # (If exists) - for video synchronization

🚀 Installation (Local Development)

    Clone the repository:

    git clone https://github.com/your-username/video-generator.git
    cd video-generator/generating_voice # Adjust if your main project folder is named differently

    Create a virtual environment:

    python -m venv venv

    Activate the virtual environment:

        On Windows:

        .\venv\Scripts\activate

        On macOS/Linux:

        source venv/bin/activate

    Install dependencies:

    pip install -r requirements.txt

    Set up Google API Key:
    Create a .env file in the root of your project (same level as app.py) and add your Google Gemini API key:

    GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"

    Remember to add .env to your .gitignore file!
    For local development, you might also need to install python-dotenv: pip install python-dotenv and add from dotenv import load_dotenv; load_dotenv() at the very top of your app.py.

    Place Assets:

        Put your reference audio files (e.g., your_voice_sample.wav) into the audios/ directory.

        Put your video backdrop files (e.g., your_backdrop_video.mp4) into the downloads/ directory.

▶️ Running Locally

Once installed and assets are in place:

    Activate your virtual environment (if not already active).

    Run the Flask application:

    python app.py

    The application will typically run on http://127.0.0.1:8000 or http://localhost:8000.

☁️ Deployment to Azure App Service

This section outlines the steps for deploying your Flask application to Azure App Service (Linux).

    Azure Setup:

        Create an Azure App Service (Linux) with a Python runtime (e.g., Python 3.13).

    Application Settings in Azure Portal:
    Navigate to your App Service in the Azure Portal -> Configuration -> Application settings.

        Add GOOGLE_API_KEY:

            Name: GOOGLE_API_KEY

            Value: YOUR_ACTUAL_GEMINI_API_KEY_FOR_AZURE

            Deployment slot setting: ✅ Check this box (if using deployment slots).

        Add SCM_DO_BUILD_DURING_DEPLOYMENT:

            Name: SCM_DO_BUILD_DURING_DEPLOYMENT

            Value: 1

            Deployment slot setting: 🔲 Uncheck this box.

    Deployment Package Creation:
    For Azure to correctly detect your application and install dependencies, ensure your deployment package is structured so that app.py, wsgi.py, and requirements.txt are at the root level of the deployed content (/home/site/wwwroot/).

        Local Steps: Go into your generating_voice folder. Select all the files and subfolders (app.py, wsgi.py, requirements.txt, audios/, templates/, downloads/, etc.). Create a ZIP file from these selected contents.

    Deploy to Azure:
    Use your preferred method (e.g., Azure CLI, Azure DevOps Pipelines, VS Code Azure Extension's "Deploy to Web App" feature) to deploy the ZIP file created in the previous step.

    Configure Startup Command:
    Navigate to your App Service in the Azure Portal -> Configuration -> General settings.

        Startup Command:

        gunicorn --bind 0.0.0.0:8000 wsgi:app

    Monitor Deployment Logs:
    After deployment, always check the Azure App Service deployment logs (under Deployment Center -> Logs) to ensure all dependencies are installed and the application starts correctly. Look for pip install -r requirements.txt output and successful Gunicorn startup messages.

🚀 Usage

The application provides a web interface (via the / route) and several API endpoints for interaction.

    GET /: Renders the main index.html page, displaying available voices and backdrops.

    POST /generate-prompt: Generates a conversational script.

        Request Body (JSON):

        {
            "topic": "space exploration",
            "style": "inspirational",
            "length": "medium"
        }

        Response (JSON):

        {
            "success": true,
            "prompt": "Your generated script goes here..."
        }

    POST /generate: Generates a single video.

        Request Body (JSON):

        {
            "prompt": "The script for your video.",
            "voice": "your_voice_sample.wav",
            "backdrop": "your_backdrop_video.mp4"
        }

        Response (JSON):

        {
            "success": true,
            "video_url": "/static/generated/video_1678888888.mp4"
        }

    POST /generate-batch: Generates multiple videos.

        Request Body (JSON):

        {
            "count": 5,             // Number of videos to generate (default: 10)
            "voice": "your_voice_sample.wav",
            "backdrop": "your_backdrop_video.mp4",
            "prompt": "Optional initial prompt for batch audio, individual video scripts will be new."
        }

        Response (JSON):

        {
            "success": true,
            "video_urls": [
                "/static/generated/batch_1678888999/video_1678888999_1.mp4",
                "...",
                "/static/generated/batch_1678888999/video_1678888999_5.mp4"
            ],
            "batch_dir": "static/generated/batch_1678888999"
        }

    GET /voices: Returns a list of available voice audio files.

    GET /backdrops: Returns a list of available video backdrop files.

    GET /audios/<filename>: Serves a specific audio file from the audios directory.

    GET /downloads/<filename>: Serves a specific video file from the downloads directory.

    GET /static/generated/<filename>: Serves a specific generated video file.

🤝 Contributing

Contributions are welcome! Please feel free to fork the repository, open issues, and submit pull requests.
📄 License

This project is licensed under the MIT License - see the LICENSE file for details. (Create a LICENSE file in your repository if you haven't already).
