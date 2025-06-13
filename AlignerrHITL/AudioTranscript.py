import whisper

def transcribe_audio(audio_path, transcript_path):
    model = whisper.load_model("base",device="cuda")  ##  ## Models ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 'large-v3-turbo', 'turbo']
    result = model.transcribe(audio_path, verbose=False)

    def format_time(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t % 1) * 1000)
        return f"{h:02}:{m:02}:{s:02}.{ms:03}"

    with open(transcript_path, "w", encoding="utf-8") as f:
        if "segments" in result:
            for segment in result["segments"]:
                start = format_time(segment["start"])
                end = format_time(segment["end"])
                text = segment["text"].strip()
                f.write(f"[{start} - {end}] {text}\n")
        else:
            f.write(result.get("text", "").strip())

    print(f"Timestamped transcript saved to: {transcript_path}")