import os
import shutil
import opensmile
from threading import Thread

from videoDL import download_video
from audioextract import extract_audio
from speechRythm_torch import analyze_speech_pattern
from SpeechPattern import flag_sensitive_words
from AudioTranscript import transcribe_audio
from soundAnalysis_torch import detect_keyboard_sounds
from BehaviorAnalysis import interpret_behavior
from Openface_Analysis import runOpenface, analyze_behavior

class HITLRunner:
    def __init__(self, output_dir=None):
        self.output_dir      = output_dir or r"C:\Users\julius\Alignerr_vids"
        os.makedirs(self.output_dir, exist_ok=True)
        self.video_path      = os.path.join(self.output_dir, "video.mp4")
        self.audio_path      = os.path.join(self.output_dir, "temp_audio.wav")
        self.transcript_path = os.path.join(self.output_dir, "transcript.txt")
        self.reference_path  = r"C:\Users\julius\Documents\vscode codes\AlignerrHITL\response_reference.txt"

    def clear_output_folder(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def run_analysis(self, video_url, progress_callback=None, status_callback=None):
        if not video_url:
            raise Exception("Video URL is missing or invalid.")

        if status_callback: status_callback("Clearing output folder...")
        self.clear_output_folder()
        if progress_callback: progress_callback(10)

        if status_callback: status_callback("Downloading video...")
        video_file = download_video(video_url, self.video_path)
        if progress_callback: progress_callback(20)

        if status_callback: status_callback("Extracting audio...")
        audio_file = extract_audio(video_file, self.audio_path)
        if progress_callback: progress_callback(30)

        if status_callback: status_callback("Extracting speech features...")
        smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.ComParE_2016,
            feature_level=opensmile.FeatureLevel.Functionals
        )
        features = smile.process_file(audio_file)
        if progress_callback: progress_callback(40)

        if status_callback: status_callback("Analyzing behavior summary...")
        behavior_summary = interpret_behavior(features)
        if progress_callback: progress_callback(50)

        # Shared result container
        thread_results = {"openface": []}

        def run_openface_task():
            if status_callback: status_callback("Running OpenFace analysis...")
            runOpenface(video_file, self.output_dir)
            if progress_callback: progress_callback(60)

            if status_callback: status_callback("Processing OpenFace results...")
            thread_results["openface"] = analyze_behavior(video_file, self.output_dir)
            if progress_callback: progress_callback(70)

        def transcribe_task():
            if status_callback: status_callback("Transcribing audio...")
            transcribe_audio(audio_file, self.transcript_path)
            if progress_callback: progress_callback(80)

        t1 = Thread(target=run_openface_task)
        t2 = Thread(target=transcribe_task)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        analyze_speech_pattern(audio_file)
        flagged_summary = flag_sensitive_words(self.transcript_path, self.reference_path)
        sound_summary = detect_keyboard_sounds(audio_file)
        if progress_callback: progress_callback(90)

        with open(self.transcript_path, "a", encoding="utf-8") as f:
            f.write("\n\n---\n\n")
            f.write("### Cheating Indicator Analysis\n")
            for item in flagged_summary:
                f.write(str(item) + "\n")

            f.write("\n### Keyboard Sound Analysis\n")
            for item in sound_summary:
                f.write(str(item) + "\n")

            f.write("\n### Behavioral Analysis\n")
            for item in behavior_summary:
                f.write(str(item) + "\n")

            f.write("\n### OpenFace Analysis\n")
            for item in thread_results["openface"]:
                f.write(str(item) + "\n")

        if status_callback: status_callback("Finalizing output...")
        if progress_callback: progress_callback(95)

        with open(self.transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read()

        try:
            os.remove(audio_file)
        except:
            pass

        if progress_callback: progress_callback(100)
        if status_callback: status_callback("Analysis complete")

        return transcript
