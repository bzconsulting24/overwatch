import subprocess
import time
import cv2
import os
import math
import sys
import pandas as pd

os.system('cls' if os.name == 'nt' else 'clear')

if os.path.exists(r"C:\Users\julius\Downloads\output\video.csv"):
    os.remove(r"C:\Users\julius\Downloads\output\video.csv")

def get_total_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total



def runOpenface(video_path, output_dir):
    path_openface = r"C:\Users\julius\OpenFace_2.2.0\FeatureExtraction.exe"
    expected_max = get_total_frames(video_path)  # set a rolling max

    # compute fps and total frames
    cap = cv2.VideoCapture(video_path)
    fps   = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    cap.release()

    # target 3 fps, max 10000 frames
    skip = max(1, int(round(fps / 3)))
    if total / skip > 10000:
        skip = math.ceil(total / 10000)

    # name of the output CSV
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    csv_path   = os.path.join(output_dir, f"{video_name}.csv")

    # build command
    command = [
        path_openface,
        '-f', video_path,
        '-out_dir', output_dir,
        '-2Dfp', '-3Dfp', '-gaze',
        '-pose', '-verbose',
        '-frame_skip', str(skip),
    ]
    print("command:", " ".join(command))

    # run subprocess with hidden window (Windows-specific)
    import subprocess
    if os.name == 'nt':  # Windows
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    try:
        while process.poll() is None:
            if os.path.exists(csv_path):
                with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    frame_count = len(lines) - 1
                    expected_max = max(expected_max, frame_count)
                    percent = int((frame_count / expected_max) * 100) if expected_max else 0
                    bar = "#" * (percent // 2)
                    sys.stdout.write(f"\r{frame_count}/{expected_max} frames  {percent:3}% |{bar:<50}|")
                    sys.stdout.flush()
            time.sleep(0.5)

        print("\n[CHECK] OpenFace completed.")
    except Exception as e:
        print(f"\n[Error] Error during processing: {e}")
        process.terminate()

    # final count
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            final_lines = f.readlines()
            final_count = len(final_lines) - 1
        print(f"\n[Check] OpenFace completed. {final_count} frames processed.")
    else:
        print("\n[Warning] OpenFace finished, but no CSV file was found.")


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
                narrative.append("The person's head remained mostly upright, indicating they stayed visually engaged with the screen.")
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

    full_report.append("")  # blank line
    full_report.append("Additional notes:")
    full_report += narrative

    # Print to console
    print("\n".join(full_report))

    # Save to file
    summary_path = os.path.join(output_dir, f"{name}_summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(full_report))

    print(f"\nSummary written to: {summary_path}")
    return results

# sample usage

test_video=r"C:\Users\julius\Downloads\video.mp4"
test_output=r"C:\Users\julius\Downloads\output"


runOpenface(test_video, test_output)
analyze_behavior(test_video, test_output)
# count_frames(test_video)
# print_frame_count(test_video)