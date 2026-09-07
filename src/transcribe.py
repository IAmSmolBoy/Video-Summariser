import os
from yt_dlp import YoutubeDL
from faster_whisper import WhisperModel
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def download(url: str):

    # Step 1: Download audio only
    print("Downloading audio...")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "audio.%(ext)s",
        "ffmpeg_location": os.getenv("FFMPEG_PATH"),
        'cookiefile': "cookies.txt",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        'socket_timeout': 60,  # Increases the read timeout limit to 60 seconds
        # "quiet": True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "video")
        duration = info.get("duration", 0)
        print(f"Downloaded: {title} ({duration // 60}m {duration % 60}s)")
        

def transcribe(model_size: str = "medium", output_file: str = "./transcript.txt"):
    
    if os.getenv("CUDA_Path"):
        os.add_dll_directory(os.getenv("CUDA_Path"))

    # Step 2: Transcribe with Whisper
    print(f"Loading Whisper ({model_size} model)...")
    model = WhisperModel(model_size, device="auto", compute_type="float16")

    print("Transcribing... (this may take a while for long videos)")
    segments, _ = model.transcribe("./audio.mp3", language="en", log_progress=True)
    
    full_transcript = " ".join([segment.text for segment in segments])
    print(full_transcript)

    # Step 3: Save transcript
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_transcript)
        
    print(f"\nDone! Saved to {output_file}")
    return full_transcript


if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        download(sys.argv[1])
    
    transcribe()