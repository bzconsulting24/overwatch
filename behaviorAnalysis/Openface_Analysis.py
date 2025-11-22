import subprocess
import time
import cv2
import os
import sys
import math
import win32gui # type: ignore
import win32con # type: ignore
import ctypes
import pandas as pd

def runOpenface(video_path, output_dir):
    # 1) compute fps & total frames
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()

    # 2) pick skip for ~3 fps, cap at 10 000 frames
    skip = max(1, int(round(fps / 3)))
    if total / skip > 10000:
        skip = math.ceil(total / 10000)

    # 3) how many frames we'll actually process (add 5% buffer for estimation errors)
    expected_max = min(int(math.ceil(total / skip) * 1.05), 10500)

    # 4) launch FeatureExtraction with tracking result window (the cool visualization!)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    csv_path = os.path.join(output_dir, f"{video_name}.csv")
    cmd = [
        r"C:\Users\julius\OpenFace_2.2.0\FeatureExtraction.exe",
        "-f",       video_path,
        "-out_dir", output_dir,
        "-2Dfp", "-3Dfp", "-pose", "-gaze",
        "-vis-track",  # Show tracking_result window with facial landmarks
        "-frame_skip", str(skip),
    ]
    proc = subprocess.Popen(cmd)

    # 5) tracking_result window will appear with the cool facial analysis visualization
    time.sleep(1)

    # 6) progress loop with timeout and 100% check
    start = time.time()
    timeout = 5 * 60
    try:
        while proc.poll() is None:
            # timeout
            if time.time() - start > timeout:
                print("\n[Warning] OpenFace timed out after 5 minutes. Terminating.")
                proc.terminate()
                break

            # progress bar
            if os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                    frame_count = len(f.readlines()) - 1

                percent = int((frame_count / expected_max) * 100)
                # terminate if percent exceeds 100%
                if percent > 100:
                    print("\n[Warning] Progress exceeded 100%. Terminating.")
                    proc.terminate()
                    break
                
                GREEN = '\033[92m'
                RESET = '\033[0m'
                blocks = percent * 50 // 100
                bar = GREEN + "#" * blocks + RESET
                sys.stdout.write(f"\r{frame_count}/{expected_max} frames  {percent:3}% |{bar:<50}|")
                sys.stdout.flush()

            time.sleep(0.5)

        print("\n[CHECK] OpenFace completed or stopped.")
    except Exception as e:
        print(f"\n[Error] {e}")
        proc.terminate()

    # 7) final count
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            final_count = len(f.readlines()) - 1
        print(f"\n[Check] OpenFace completed. {final_count} frames processed.")
    else:
        print("\n[Warning] no CSV found after OpenFace.")


def analyze_behavior(video_path, output_dir):
    name = os.path.splitext(os.path.basename(video_path))[0]
    data_file = os.path.join(output_dir, f"{name}.csv")
    results = []
    narrative = []

    try:
        df = pd.read_csv(data_file)
        df.columns = df.columns.str.strip()

        # Head pose analysis Rx (roll)
        # Note: pose_Rx is typically used for roll, but we also check pose_Ry for pitch
        # Head pitch (Rx)
        if 'pose_Rx' in df.columns:
            downward_ratio = (df['pose_Rx'] < -0.2).sum() / len(df)
            if downward_ratio > 0.2:
                results.append("The person frequently looked downward during the interview. This behavior may suggest they were referring to notes or avoiding eye contact.")
            else:
                narrative.append("The persons head remained mostly upright, indicating they stayed visually engaged with the screen.")
        else:
            narrative.append("Head pitch data was not available for analysis.")
        
        # Head yaw (Ry)
        if 'pose_Ry' in df.columns:
            turning_ratio = (df['pose_Ry'].abs() > 0.3).sum() / len(df)
            if turning_ratio > 0.2:
                results.append("The person frequently turned their head away from the screen, which may suggest distraction or external reference.")
            else:
                narrative.append("The person generally kept their face oriented toward the screen.")
        else:
            narrative.append("Head yaw data was not available for analysis.")


        # Head roll (Rz)
        if 'pose_Rz' in df.columns:
            tilt_ratio = (df['pose_Rz'].abs() > 0.3).sum() / len(df)
            if tilt_ratio > 0.2:
                results.append("The person frequently tilted their head sideways, which could indicate discomfort or posture imbalance.")
            else:
                narrative.append("The person’s head remained level without excessive side tilting.")
        else:
            narrative.append("Head roll data was not available for analysis.")

        # Blinking analysis
        if 'AU45_r' in df.columns:
            blink_rate = (df['AU45_r'] > 0.5).sum() / len(df)
            if blink_rate < 0.01:
                results.append("The person barely blinked. This may be unnatural, like staring at something, such as a script.")
            else:
                narrative.append("The person blinked at a rate consistent with normal human behavior.")
        else:
            narrative.append("Blinking activity could not be measured.")

        # Gaze direction analysis
        if 'gaze_angle_x' in df.columns and 'gaze_angle_y' in df.columns:
            offscreen_ratio = ((df['gaze_angle_x'].abs() > 0.4) | (df['gaze_angle_y'].abs() > 0.4)).sum() / len(df)
            if offscreen_ratio > 0.2:
                results.append("The person frequently looked away from the screen. This may suggest they were distracted or referencing information off-camera.")
            else:
                narrative.append("The person maintained steady gaze toward the screen for most of the session.")
        else:
            narrative.append("Gaze direction could not be assessed.")

    except Exception as e:
        results.append("Behavioral data could not be analyzed due to a processing error.")

    # Compose report
    full_report = []

    if results:
        full_report.append("Behavioral observations suggest the following areas of concern:")
        full_report += results
    else:
        full_report.append("No unusual behavior was observed. The person appeared naturally engaged throughout the session.")
    
    return full_report, narrative