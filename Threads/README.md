# alignerr_peeps.py

This script performs automated analysis on a video:

- Downloads a video URL or uses a local file
- Extracts evenly spaced frames and timestamps them
- Bundles frames into a PDF
- Extracts audio and runs:
  - Whisper transcription with timestamps
  - Speech rhythm analysis
  - Keyboard sound detection
  - Behavioral feature extraction and interpretation
  - Sensitive-word flagging in transcript

---

## Prerequisites

1. Python 3.8 or newer
2. Install Python dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Download the PANNs model checkpoint and place it under a `panns_data/` folder:

   ```text
   Threads/panns_data/Cnn14_mAP=0.431.pth
   ```

   You can get the checkpoint from the official PANNs repository:
   https://github.com/qiuqiangkong/panns_inference

---

## Usage

```powershell
python alignerr_peeps.py
```

- Enter the video URL at the prompt (or modify the script to use a local file).
- Outputs are saved to `C:\Users\julius\Alignerr_vids\threads` by default.

---

## Configuration

- To change number of frames, resolution, or output folder paths, edit the constants at the top of the script.
- Flagged words can be customized in the `flag_sensitive_words()` call.

Enjoy your analysis!
