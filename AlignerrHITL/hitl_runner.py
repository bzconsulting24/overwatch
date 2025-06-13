def run_hitl_analysis(video_url):
    import os
    import shutil
    import opensmile
    # port analyze_speech_pattern
    from speechRythm_torch import analyze_speech_pattern
    from SpeechPattern import flag_sensitive_words
    from AudioTranscript import transcribe_audio
    # from soundAnalysis import detect_keyboard_sounds
    from soundAnalysis_torch import detect_keyboard_sounds
    from BehaviorAnalysis import interpret_behavior
    # from pdfCompile import extract_even_frames_with_timestamps, save_frames_to_pdf_and_cleanup
    from Openface_Analysis import runOpenface, analyze_behavior
    from videoDL import download_video
    from audioextract import extract_audio

    os.system('cls')
    os.environ["OPENCV_FFMPEG_READ_ATTEMPTS"] = "20000"  # Increase attempts to read video frames

    def clear_output_folder(folder_path):
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)

        
    if __name__ == "__main__":
        # === SETTINGS ===
        use_url = True  # Set to False to use a local video file
        # video_url = input("Enter video URL:")
        local_video_path = r"C:\Users\julius\Alignerr_vids\video.mp4"
        download_target = r"C:\Users\julius\Alignerr_vids\video.mp4"
        
        output_dir = r"C:\Users\julius\Alignerr_vids"
        audio_path = os.path.join(output_dir, "temp_audio.wav")
        transcript_path = os.path.join(output_dir, "transcript.txt")

        clear_output_folder(output_dir)
        video_path = download_video(video_url, download_target) if use_url else local_video_path

        # extract_even_frames_with_timestamps(video_path, output_dir)
        
    # --- extract audio and get back a path or None
    audio_file = extract_audio(video_path, audio_path)

    smile = opensmile.Smile(
        feature_set=opensmile.FeatureSet.ComParE_2016,
        feature_level=opensmile.FeatureLevel.Functionals
    )

    if audio_file:
        # good WAV, do feature extraction
        features = smile.process_file(audio_file)
    else:
        # no audio: skip this step
        print("Bypassing audio analysis.")
        features = None

    print(features.head() if features is not None else "No audio features")
    # print(features.filter(regex="F0|jitter|energy", axis=1).head())  ## For debugging
    if features is not None:
        behavior_summary = interpret_behavior(features)
    else:
        print("Skipping behavior analysis (no audio features).")
        behavior_summary = []
    ##  Run Openface
    runOpenface(video_path, output_dir)
    Openface_summary = analyze_behavior(video_path, output_dir)

    if os.path.exists(audio_path):
        transcribe_audio(audio_path, transcript_path)
        analyze_speech_pattern(audio_path)
        flagged_summary = flag_sensitive_words(transcript_path)
        sound_summary = detect_keyboard_sounds(audio_path)         

    ## Append summaries to the transcript file
        with open(transcript_path, "a", encoding="utf-8") as f:
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


        os.remove(audio_path)
        # os.remove(video_path)
        os.startfile(output_dir)
        print("Temp audio and video files deleted.")
    else:
        print("[X] Skipping analysis: audio file not found.")

