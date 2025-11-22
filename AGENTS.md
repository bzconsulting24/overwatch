# Repository Guidelines

## Project Structure & Module Organization
- `behaviorAnalysis/`: main PyQt HITL app (`main.py`) plus pipeline orchestrator (`hitl_runner.py`) that downloads media, extracts audio, runs speech/behavior/OpenFace analysis, and writes outputs to `HITLRunner.output_dir` (set this to a writable local folder such as `./out`).
- `Threads/`: experimental audio/alignment utilities (`alignerr_peeps.py`, `data_gen.py`) with its own `requirements.txt`.
- `VideoFrame_analyer/MainAnalyzer.py`: frame-level analyzer prototype; `Trimmer/trimmer.py`: small trimming helper.
- Root scripts like `Openface_Analysis.py` and `convert.py` support the pipeline; avoid committing generated media, transcripts, or downloaded model files.

## Environment, Build, and Run
- Use Python 3.10+ with a virtualenv:
  ```
  python -m venv .venv && source .venv/bin/activate
  pip install -r behaviorAnalysis/requirements.txt
  # optional: pip install -r Threads/requirements.txt  # for aligner tools
  ```
- Launch the GUI: `python behaviorAnalysis/main.py` (requires PyQt5). Update `HITLRunner(output_dir=...)` before running to control where artifacts are written.
- Quick headless check of the runner:
  ```python
  from behaviorAnalysis.hitl_runner import HITLRunner
  HITLRunner("./out").run_analysis("<video_url>")
  ```

## Coding Style & Naming Conventions
- Python: 4-space indents; `snake_case` for functions/vars; `PascalCase` for classes; keep functions small and side-effect aware.
- Centralize path/config constants near module tops and prefer passing them into `HITLRunner` instead of hard-coding.
- Add docstrings and type hints for new public functions; prefer `logging` over bare `print` for new code, while preserving UI callbacks (`status_callback`, `progress_callback`).

## Testing Guidelines
- No formal suite yet. Add `pytest` cases for logic-heavy helpers (speech flagging, audio feature transforms) and keep fixtures minimal.
- Manual check: run `python behaviorAnalysis/main.py` with a short video URL, confirm the transcript, cheating indicators, keyboard analysis, and OpenFace summaries are appended to the output transcript file in your chosen `output_dir`.

## Commit & Pull Request Guidelines
- Follow the existing imperative style with optional Conventional Commit prefixes (`feat:`, `fix:`, `refactor:`). Keep titles concise; add a short body describing rationale and risks.
- For PRs: include a brief summary, commands/tests run, any config/path changes (e.g., `output_dir`, API keys), and screenshots/GIFs for UI changes.

## Security & Configuration Tips
- Do not commit credentials or service JSON. Google Cloud Speech uses `GOOGLE_APPLICATION_CREDENTIALS` pointing to a local key file.
- Model downloads (Whisper, OpenFace, opensmile) occur at runtime; do not vendor weights. Ensure `.gitignore` covers generated media, transcripts, cache directories, and temp audio.
