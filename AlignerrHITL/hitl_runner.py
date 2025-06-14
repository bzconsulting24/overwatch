class HITLRunner:
    def __init__(self, output_dir=None, result_box=None):
        import os
        import shutil
        self.os = os
        self.shutil = shutil
        self.output_dir = output_dir or r"C:\Users\julius\Alignerr_vids"
        self.result_box = result_box
        self.audio_path = self.os.path.join(self.output_dir, "temp_audio.wav")
        self.download_target = self.os.path.join(self.output_dir, "video.mp4")
        self.transcript_path = self.os.path.join(self.output_dir, "transcript.txt")

        if not self.os.path.exists(self.output_dir):
            self.os.makedirs(self.output_dir, exist_ok=True)

    def clear_output_folder(self):
        if self.os.path.exists(self.output_dir):
            self.shutil.rmtree(self.output_dir)
        self.os.makedirs(self.output_dir, exist_ok=True)

    def run_analysis(self, video_url, progress_callback=None, status_callback=None):
        from videoDL import download_video
        from audioextract import extract_audio

        if not video_url:
            raise Exception("Video URL is missing or invalid.")

        if status_callback:
            status_callback.emit("Clearing output folder...")
        self.clear_output_folder()
        if progress_callback:
            progress_callback.emit(10)

        if status_callback:
            status_callback.emit("Downloading video...")
        try:
            video_path = download_video(video_url, self.download_target)
            if not video_path or not self.os.path.exists(video_path):
                raise Exception("Video download failed or file not found.")
        except Exception as e:
            if status_callback:
                status_callback.emit(f"Error downloading video: {e}")
            raise Exception(f"Video download failed: {e}")

        if progress_callback:
            progress_callback.emit(20)

        if status_callback:
            status_callback.emit("Extracting audio...")
        try:
            audio_file = extract_audio(video_path, self.audio_path or None)
        except Exception as e:
            if status_callback:
                status_callback.emit(f"Error extracting audio: {e}")
            raise Exception(f"Audio extraction failed: {e}")

        if progress_callback:
            progress_callback.emit(30)

        import os
        import shutil
        import opensmile
        from speechRythm_torch import analyze_speech_pattern
        from SpeechPattern import flag_sensitive_words
        from AudioTranscript import transcribe_audio
        from soundAnalysis_torch import detect_keyboard_sounds
        from BehaviorAnalysis import interpret_behavior
        from Openface_Analysis import runOpenface, analyze_behavior

        os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "20000"

        def clear_output_folder(folder_path):
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
            os.makedirs(folder_path, exist_ok=True)

        if __name__ == "__main__":
            use_url = True
            video_url = self.ui.lineEdit_url.text().strip()
            local_video_path = r"C:\Users\julius\Alignerr_vids\video.mp4"
            download_target = r"C:\Users\julius\Alignerr_vids\video.mp4"

            output_dir = r"C:\Users\julius\Alignerr_vids"
            audio_path = os.path.join(output_dir, "temp_audio.wav")
            transcript_path = os.path.join(output_dir, "transcript.txt")

            clear_output_folder(output_dir)
            if progress_callback:
                progress_callback.emit(10)

            video_path = download_video(video_url, download_target) if use_url else local_video_path
            if progress_callback:
                progress_callback.emit(20)

        audio_file = extract_audio(video_path, self.audio_path)
        if progress_callback:
            progress_callback.emit(30)

        smile = opensmile.Smile(
            feature_set=opensmile.FeatureSet.ComParE_2016,
            feature_level=opensmile.FeatureLevel.Functionals
        )

        if audio_file:
            features = smile.process_file(audio_file)
            if progress_callback:
                progress_callback.emit(40)
        else:
            features = None

        if features is not None:
            behavior_summary = interpret_behavior(features)
            if progress_callback:
                progress_callback.emit(50)
        else:
            behavior_summary = []

        runOpenface(video_path, self.output_dir)
        if progress_callback:
            progress_callback.emit(60)

        Openface_summary = analyze_behavior(video_path, self.output_dir)
        if progress_callback:
            progress_callback.emit(70)

        if os.path.exists(self.audio_path):
            transcribe_audio(self.audio_path, self.transcript_path)
            if progress_callback:
                progress_callback.emit(80)

            analyze_speech_pattern(self.audio_path)
            flagged_summary = flag_sensitive_words(self.transcript_path)
            sound_summary = detect_keyboard_sounds(self.audio_path)
            if progress_callback:
                progress_callback.emit(90)

            with open(self.transcript_path, "a", encoding="utf-8") as f:
                f.write("\n\n---\n\n")
                f.write(" ### Cheating indicator Analysis\n\n")
                for line in flagged_summary:
                    f.write(str(line) + "\n")
                f.write("\n")
                for line in sound_summary:
                    f.write(str(line) + "\n")
                f.write("\n")
                f.write("### Behavioral Analysis\n\n")
                for line in behavior_summary:
                    f.write(str(line) + "\n")
                f.write("\n")
                f.write("### OpenFace Analysis\n\n")
                for line in Openface_summary:
                    f.write(str(line) + "\n")

            if progress_callback:
                progress_callback.emit(95)

            os.remove(self.audio_path)
            if self.os.path.exists(self.transcript_path):
                with open(self.transcript_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(content)
                    if self.result_box:
                        self.result_box.setPlainText(content)
