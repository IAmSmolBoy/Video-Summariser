import os
from yt_dlp import YoutubeDL
from faster_whisper import BatchedInferencePipeline, WhisperModel
import sys
from dotenv import load_dotenv
from pathlib import Path
import shutil

# Load environment variables from .env file
load_dotenv()
    
AUDIO_DIR = "audios"

def download(url: str):
    
    # Delete the folder and all its contents
    if os.path.exists(AUDIO_DIR):
        shutil.rmtree(AUDIO_DIR)

    # Recreate the empty folder
    os.makedirs(AUDIO_DIR)

    # Step 1: Download audio only
    print("Downloading audio...")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{AUDIO_DIR}/%(title)s.%(ext)s",
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
    
    # Wrap in the pipeline for fast chunked processing
    batched_model = BatchedInferencePipeline(model=model)

    # Specify the directory path
    dir_path = Path(AUDIO_DIR)
    
    full_transcript = ""
    
    # Sort files alphbetically
    audios = sorted([f for f in dir_path.iterdir() if f.is_file()], key=lambda x: x.name)

    # Loop through all files inside it
    for item in audios:
        if item.is_file():

            print("Transcribing...")
            segments, _ = batched_model.transcribe(
                item,
                language="en",
                log_progress=True,
                batch_size=8,                         # Cap at 8 to prevent 6GB VRAM OOM crashes
                beam_size=1,                          # Greedy decoding for absolute maximum speed
                vad_filter=True,                      # Cut out silence to save massive compute time
                without_timestamps=True               # Drop token overhead for faster generation
            )
            
            full_transcript += " ".join([segment.text for segment in segments]) + "\n"
            print(full_transcript)

    # Step 3: Save transcript
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_transcript.replace(". ", ".\n"))
        
    print(f"\nDone! Saved to {output_file}")
    return full_transcript


if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        download(sys.argv[1])
    
    transcribe()