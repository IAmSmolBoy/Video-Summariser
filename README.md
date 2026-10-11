# Video Summariser

Download a YouTube video's audio, transcribe it locally with Whisper, then summarise the
transcript into raw Markdown with Google Gemini.

## Pipeline

| Stage | Script | Tool | Output |
| --- | --- | --- | --- |
| 1. Download audio | [src/transcribe.py](src/transcribe.py) `download()` | `yt-dlp` + FFmpeg | `audio.mp3` |
| 2. Transcribe | [src/transcribe.py](src/transcribe.py) `transcribe()` | `faster-whisper` | `transcript.txt` |
| 3. Summarise | [src/summarise.py](src/summarise.py) `summarise()` | Gemini (`MODEL` in `config.yaml`) | `out.md` (and `summaries.md` for long videos) |

Running `src.summarise` executes all three stages. Running `src.transcribe` stops after stage 2.

## Prerequisites

- **Python 3.8+**
- **FFmpeg** — required to extract MP3 audio. Install from
  [ffmpeg.org](https://ffmpeg.org/download.html), via `apt-get install ffmpeg` (Linux) or
  `brew install ffmpeg` (macOS).
- **Gemini API key** — from [Google AI Studio](https://aistudio.google.com/apikey). Only
  needed for the summarise stage.
- **(Optional) NVIDIA CUDA toolkit** — enables GPU-accelerated transcription. Without a GPU,
  Whisper falls back to CPU automatically.
- **(Optional) `cookies.txt`** — a Netscape-format cookie file in the project root, used by
  `yt-dlp` for age-restricted or members-only videos.

## Installation

```bash
pip install -r src/requirements.txt
```

Dependencies: `faster-whisper`, `google-genai`, `python-dotenv`, `yt-dlp`.

## Configuration

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
FFMPEG_PATH=/path/to/ffmpeg/bin
CUDA_Path=C:\path\to\CUDA\vXX.X\bin\x64
```

| Variable | Required | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | For summarising | Authenticates the Gemini Developer API. |
| `FFMPEG_PATH` | For downloading | Directory containing the FFmpeg binary, passed to `yt-dlp`. |
| `CUDA_Path` | Optional | Directory of CUDA DLLs; added to the DLL search path for GPU transcription. |

### `config.yaml`

Pipeline settings live in `config.yaml` in the project root. Both scripts read it on
startup, so it must exist and the scripts must be run from the project root.

```yaml
INSTRUCTIONS: Summarize this chronologically in bullet points with section headers that include an emoji in raw markdown
MODEL: gemini-3.7-flash
THINKING: medium
TOKEN_LIMIT: 100000
AUDIO_DIR: audios
```

| Key | Used by | Purpose |
| --- | --- | --- |
| `INSTRUCTIONS` | `summarise.py` | Prompt appended to the transcript in each Gemini call. |
| `MODEL` | `summarise.py` | Gemini model name. |
| `THINKING` | `summarise.py` | Gemini thinking level: `low`, `medium` or `high`. |
| `TOKEN_LIMIT` | `summarise.py` | Character count above which the transcript is split into chunks. |
| `AUDIO_DIR` | `transcribe.py` | Folder the audio is downloaded to (emptied before each download). |

## Usage

Run the scripts as modules **from the project root** (they import `src.transcribe`):

**Full pipeline — download, transcribe, summarise:**

```bash
python src/summarise.py "https://www.youtube.com/watch?v=..."
```

**Summarise audio you already have** (place `audio.mp3` in the project root, omit the URL):

```bash
python src/summarise.py
```

**Transcribe only (no Gemini key needed):**

```bash
python src/transcribe.py "https://www.youtube.com/watch?v=..."
```

The first argument is treated as a video URL only if it starts with `http`; otherwise the
scripts expect an existing `audio.mp3`.

## Output files

All written to the project root:

- **`audios/audio.mp3`** — extracted audio (192 kbps MP3); the folder is set by `AUDIO_DIR`.
- **`transcript.txt`** — full plain-text transcript.
- **`summaries.md`** — intermediate per-chunk summaries (only created for transcripts over
  ~100,000 characters).
- **`out.md`** — final Markdown summary: chronological bullet points under emoji section
  headers (format controlled by `INSTRUCTIONS`). Overwritten on each run.

## How it works

**Transcription** ([src/transcribe.py](src/transcribe.py)) uses the `faster-whisper`
`medium` model with `device="auto"` and `float16` compute, forced to English. Adjust the
model size or output path via the `model_size` / `output_file` arguments to `transcribe()`.

**Summarisation** ([src/summarise.py](src/summarise.py)) strips timestamp lines
(`MM:SS ...`) from the transcript, then:

- If under `TOKEN_LIMIT` (100,000 characters by default) it makes a single Gemini call and writes
  `out.md`.
- Otherwise it splits the text into ~100,000-character chunks on word boundaries, summarises
  each chunk into `summaries.md`, then summarises that combined file into `out.md`.

The prompt, model, thinking level and character limit are set in `config.yaml`.

## Troubleshooting

- **`python` not recognised** — restart your terminal after installing Python.
- **FFmpeg not found** — check `FFMPEG_PATH` points to the directory containing the binary.
- **Download fails** — verify the URL is valid and public; for restricted videos supply a
  `cookies.txt` in the project root.
- **Import error for `src.transcribe`** — run the scripts with `python -m src.summarise`
  from the project root, not `python src/summarise.py`.
- **Summary step fails** — confirm `GEMINI_API_KEY` is set and valid, and that `MODEL` in
  `config.yaml` is a valid Gemini model name.
- **`FileNotFoundError: config.yaml`** — run the scripts from the project root, where
  `config.yaml` lives.
- **Slow transcription** — expected on CPU for long videos; set up CUDA and `CUDA_Path`, or
  use a smaller Whisper model.
- **`TypeError: open() got an unexpected keyword argument 'metadata_errors'`** — the
  installed PyAV version is too new; downgrade it with `pip install "av<19"`.