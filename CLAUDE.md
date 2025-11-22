# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Overwatch is a behavior analysis tool designed to analyze videos for behavioral indicators, speech patterns, and non-verbal cues. The system processes video/audio content through multiple analysis pipelines including:
- Audio transcription with speaker diarization (Google Speech-to-Text with Whisper fallback)
- Speech pattern and rhythm analysis (PyTorch-based tempo/volume variation)
- Keyboard sound detection (acoustic analysis for typing sounds)
- Facial analysis via OpenFace (AU detection, gaze, pose)
- Voice feature extraction via openSMILE (pitch, energy, jitter)

The project supports both a PyQt5 desktop application and a FastAPI web service with async job management.

## Development Setup

### Environment
This project uses Python 3.11+ with a virtual environment. Main dependencies include:
- PyTorch 2.7.1 (with CUDA support for GPU acceleration)
- TensorFlow 2.18.0
- FastAPI 0.115.0 / Uvicorn 0.30.6
- OpenAI Whisper, openSMILE, librosa, mediapipe

```bash
# Install all dependencies
pip install -r behaviorAnalysis/requirements.txt
```

### External Dependencies (Windows-specific)
- **OpenFace 2.2.0**: Windows facial analysis binary at `C:\Users\julius\OpenFace_2.2.0\FeatureExtraction.exe`
- **FFmpeg/FFprobe**: System-wide installation required for video/audio processing
- **Google Cloud credentials**: JSON keyfile for Speech-to-Text API (path: `C:\Users\julius\Documents\vscode codes\behaviorAnalysis\soy-lore-465001-s6-e153c4da9d23.json`)
  - Bucket name: `audiodiarize`
  - NEVER commit this file to version control

## Running the Application

### Desktop Application (PyQt5)
```bash
cd behaviorAnalysis
python main.py
```

The GUI (`main.py`) provides:
- URL input field for video source
- Progress bar with real-time status updates
- Text viewer for analysis results
- Threading-based non-blocking UI using PyQt5 QThread and Worker pattern

### FastAPI Server
```bash
cd behaviorAnalysis
python api_server.py
# or
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

API Endpoints:
- `POST /api/analyze` - Submit analysis job, returns `{"jobId": "<uuid>"}`. Accepts `{"videoUrl": "...", "outputDir": "...", "modelHint": "..."}`
- `GET /api/analyze/{job_id}` - Poll job status/progress, returns `{"status": "...", "progress": 0-100, "transcript": "...", "result": {...}}`
- `GET /health` - Health check, returns `{"ok": true}`

Job Management:
- In-memory job store using `Dict[str, JobState]` (replace with Redis/DB for production)
- ThreadPoolExecutor with max 2 workers for parallel job processing
- Jobs run in background threads via `loop.run_in_executor()`

### Docker (Note: Limited functionality)
```bash
docker build -f behaviorAnalysis/Dockerfile -t overwatch .
docker run -p 8000:8000 overwatch
```

**Important**: Docker deployment lacks OpenFace binary and Google Cloud credentials, so facial analysis and diarized transcription will not work. Use for API structure testing only.

## Architecture

### Analysis Pipeline (`hitl_runner.py`)
The `HITLRunner` class orchestrates the full analysis pipeline in `hitl_runner.py:34-155`. Key execution flow:

1. **Initialization & Cleanup** (Progress: 0-10%)
   - Clears output directory via `clear_output_folder()` using `shutil.rmtree()`
   - Sets up paths: `video_path`, `audio_path`, `transcript_path`, `reference_path`

2. **Video Download & Audio Extraction** (Progress: 10-25%) - `AudioVideoTreadingDL.py`
   - Downloads video from URL using `ffmpeg` with copy codec
   - Extracts audio as WAV simultaneously using threading (parallel download)
   - Uses `ffprobe` to determine video duration for progress tracking
   - Displays progress bar via `subprocess.Popen()` monitoring `out_time_us` from ffmpeg

3. **Speech Feature Extraction** (Progress: 25-40%)
   - Uses openSMILE ComParE_2016 feature set (6,373 features)
   - Extracts acoustic features: pitch, energy, jitter, spectral features
   - Returns pandas DataFrame with functional statistics (mean, std, percentiles)

4. **Behavior Summary** (Progress: 40-50%)
   - Interprets openSMILE features via `BehaviorAnalysis.interpret_behavior()`
   - Generates text summaries of pitch, energy, jitter characteristics

5. **Parallel Processing Phase** (Progress: 50-80%) - Two concurrent threads:
   - **Thread 1 (OpenFace)**:
     - Runs `Openface_Analysis.runOpenface()` → subprocess to OpenFace binary
     - Processes at 3fps (frame_skip calculated from video fps), max 10k frames
     - Generates CSV with AU intensities, gaze vectors, pose (Rx, Ry, Rz)
     - Analyzes CSV via `analyze_behavior()` for head movement, gaze patterns
   - **Thread 2 (Transcription)**:
     - Uploads audio to Google Cloud Storage bucket `audiodiarize`
     - Calls Google Speech-to-Text API with `SpeakerDiarizationConfig` (2-10 speakers)
     - Writes diarized transcript with speaker labels to `transcript.txt`
     - **Fallback**: If diarization fails, loads Whisper `base` model on CUDA and generates speaker-agnostic transcript

6. **Sequential Post-Processing** (Progress: 80-90%)
   - `speechRythm_torch.py`: PyTorch-based tempo/volume variation analysis
   - `SpeechPattern.py`: Flags sensitive words by comparing transcript against `response_reference.txt`
   - `soundAnalysis.py`: Detects keyboard/typing sounds via acoustic signature matching

7. **Output Compilation** (Progress: 90-100%)
   - Appends all analysis results to `transcript.txt` in sections:
     - Cheating Indicator Analysis (flagged words)
     - Keyboard Sound Analysis
     - Behavioral Analysis (openSMILE interpretation)
     - OpenFace Analysis (facial behavior)
   - Cleans up temporary audio file
   - Returns full transcript string

### Module Responsibilities

**Core Pipeline:**
- **`hitl_runner.py`**: Main orchestrator, defines `HITLRunner` class with `run_analysis()` method
- **`AudioVideoTreadingDL.py`**: Parallel ffmpeg download/extraction using Python `threading` module
- **`google_transcribe.py`**: Google Cloud Speech-to-Text client with diarization, bucket cleanup, speaker mapping

**Analysis Modules:**
- **`speechRythm_torch.py`**: PyTorch-based speech tempo/volume variation detection
- **`soundAnalysis.py`**: Keyboard/typing sound detection via acoustic analysis
- **`BehaviorAnalysis.py`**: Interprets openSMILE features (pitch, energy, jitter) into text summaries
- **`SpeechPattern.py`**: Flags suspicious/sensitive words by diff against `response_reference.txt`
- **`Openface_Analysis.py`**: Wrapper for OpenFace binary, includes Windows `win32gui` window management to hide OpenFace GUI

**User Interfaces:**
- **`api_server.py`**: FastAPI app with async job management (`ThreadPoolExecutor`, UUID-based job tracking)
- **`main.py`**: PyQt5 GUI with QThread/Worker pattern for non-blocking analysis
- **`hitl_app_copy_ui.py`**: Auto-generated Qt Designer UI file for `main.py`

**Utilities:**
- **`Threads/`**: Data generation and visualization utilities (separate from main pipeline)
- **`Trimmer/trimmer.py`**: Video trimming utility
- **`VideoFrame_analyer/MainAnalyzer.py`**: Frame-by-frame analysis tool
- **`convert.py`**: Rubric JSON to CSV converter

### Key Design Patterns

1. **Callback-driven progress reporting**:
   - `progress_callback(percent: int)` updates GUI progressBar or API job state
   - `status_callback(message: str)` updates status text in real-time
   - Callbacks threaded through entire pipeline from UI → HITLRunner → analysis modules

2. **Parallel I/O with Python threading**:
   - `AudioVideoTreadingDL.py` runs video/audio download in parallel threads
   - `hitl_runner.py` runs OpenFace + transcription in parallel (lines 111-116)
   - Thread synchronization via `thread.join()` before sequential post-processing

3. **Graceful degradation**:
   - Google transcription fails → Whisper fallback (try/except in `hitl_runner.py:79-109`)
   - `google_transcribe.py` checks `GOOGLE_CLOUD_AVAILABLE` flag, provides dummy classes if imports fail

4. **Subprocess management**:
   - OpenFace runs as subprocess with `subprocess.Popen()`, stderr parsing for progress
   - ffmpeg/ffprobe invoked via `subprocess.check_output()` and `subprocess.Popen()` with progress monitoring
   - Windows-specific window hiding via `win32gui.EnumWindows()` and `win32gui.ShowWindow()`

5. **Hardcoded paths** (Windows-centric):
   - Default output: `C:\Users\julius\Alignerr_vids`
   - OpenFace binary: `C:\Users\julius\OpenFace_2.2.0\FeatureExtraction.exe`
   - Google Cloud keyfile: `C:\Users\julius\Documents\vscode codes\behaviorAnalysis\soy-lore-465001-s6-e153c4da9d23.json`
   - Reference text: `C:\Users\julius\Documents\vscode codes\behaviorAnalysis\response_reference.txt`

## Important Notes

### Platform Dependencies
- **Windows-only**: OpenFace binary and `win32gui`/`win32con` for window hiding make this Windows-specific
- **GPU acceleration**: Whisper fallback uses `device="cuda"` (line 91), PyTorch models benefit from CUDA
- **System requirements**: FFmpeg/FFprobe must be in system PATH

### Configuration Points
- **Output directory**: `HITLRunner(output_dir="...")` parameter or default `C:\Users\julius\Alignerr_vids`
- **Reference text path**: `C:\Users\julius\Documents\vscode codes\behaviorAnalysis\response_reference.txt` (used by `SpeechPattern.py`)
- **OpenFace binary**: `C:\Users\julius\OpenFace_2.2.0\FeatureExtraction.exe` (hardcoded in `Openface_Analysis.py:23`)
- **Google Cloud keyfile**: `C:\Users\julius\Documents\vscode codes\behaviorAnalysis\soy-lore-465001-s6-e153c4da9d23.json` (hardcoded in `google_transcribe.py:22`)
- **GCS bucket**: `audiodiarize` (hardcoded in `google_transcribe.py:21`)

### API Job Management
- In-memory job store (`jobs: Dict[str, JobState]` in `api_server.py:28`)
- **Not production-ready**: Jobs lost on server restart, no job cleanup/expiration
- For production: Replace with Redis, PostgreSQL, or persistent queue system
- Max 2 concurrent jobs (`ThreadPoolExecutor(max_workers=2)` in `api_server.py:29`)

## Common Development Workflows

### Adding a New Analysis Module
1. Create module in `behaviorAnalysis/` with function signature:
   ```python
   def analyze_feature(audio_path: str) -> List[str]:
       # Returns list of text summary lines
       return ["Analysis result 1", "Analysis result 2"]
   ```
2. Import in `hitl_runner.py` (top of file)
3. Call in `HITLRunner.run_analysis()` at appropriate progress point
4. Append results to `transcript.txt` in compilation block (lines 123-139):
   ```python
   f.write("\n### New Analysis Name\n")
   for item in new_analysis_results:
       f.write(str(item) + "\n")
   ```
5. Update progress percentages if needed

### Modifying the Analysis Pipeline
Edit `HITLRunner.run_analysis()` in `hitl_runner.py:34-155`:
- **Add/remove steps**: Insert new analysis calls before/after existing ones
- **Adjust progress**: Ensure all `progress_callback()` calls sum to logical flow (currently 10→25→40→50→80→90→100)
- **Parallelize new step**: Add to existing threads (lines 111-116) or create new thread, ensure `thread.join()` before dependent steps
- **Change output format**: Modify compilation block (lines 123-139)

### Debugging Pipeline Issues
1. **Check progress callbacks**: Ensure each module calls `progress_callback()` and `status_callback()` if provided
2. **OpenFace fails**: Verify binary path, check CSV output in `output_dir`
3. **Transcription fails**: Check Google Cloud credentials, bucket permissions; fallback should trigger Whisper
4. **Threading deadlocks**: Verify all threads have corresponding `.join()` calls

### Working with Hardcoded Paths
To make code portable:
1. Extract paths to constants at top of file or config file
2. Use `os.path.join()` for cross-platform compatibility
3. Add environment variable fallbacks: `os.getenv("OPENFACE_PATH", default_path)`
4. For production: Use `.env` file with `python-dotenv`

## Output Structure

### Generated Files (in output_dir)
- **`transcript.txt`**: Main output with all analysis results in sections
- **`video.mp4`**: Downloaded video (persists after analysis)
- **`temp_audio.wav`**: Extracted audio (deleted at end via `os.remove()`)
- **`video.csv`**: OpenFace output with AU intensities, gaze, pose per frame

### transcript.txt Format
```
[Timestamp] [SPEAKER_X] Transcribed speech...
[Timestamp] [SPEAKER_Y] Transcribed speech...

---

### Cheating Indicator Analysis
Flagged word: "..."

### Keyboard Sound Analysis
Keyboard detected at: ...

### Behavioral Analysis
Pitch: ...
Energy: ...

### OpenFace Analysis
Head movement: ...
Gaze patterns: ...
```

## Data Files Reference

- **`Rubric.json`**: Scoring rubric for evaluation (document assessment - not used in main pipeline)
- **`response_reference.txt`**: Reference text for word flagging via `SpeechPattern.py` (NOT in version control)
- **`convert.py`**: Utility to convert `Rubric.json` → CSV format
