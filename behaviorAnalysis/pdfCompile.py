import os
from PIL import Image
import cv2
import numpy as np

def extract_even_frames_with_timestamps(video_path, output_folder, num_frames=200, resize_width=640, resize_height=360):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Failed to open video: {video_path}")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

    for count, i in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        success, frame = cap.read()
        if not success:
            continue

        timestamp_sec = i / fps
        minutes = int(timestamp_sec // 60)
        seconds = int(timestamp_sec % 60)
        millis = int((timestamp_sec % 1) * 1000)
        timestamp_text = f"{minutes:02d}:{seconds:02d}.{millis:03d}"

        frame_resized = cv2.resize(frame, (resize_width, resize_height))
        cv2.putText(frame_resized, timestamp_text, (10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8,
                    color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)

        frame_filename = os.path.join(output_folder, f"frame_{count:02d}.webp")
        cv2.imwrite(frame_filename, frame_resized)

    cap.release()
    print(f"Saved {num_frames} timestamped frames to: {output_folder}")
    

def save_frames_to_pdf_and_cleanup(output_folder, pdf_filename="video_frames.pdf"):
    images = sorted([
        os.path.join(output_folder, f)
        for f in os.listdir(output_folder)
        if f.startswith("frame_") and f.endswith(".webp")
    ])
    if not images:
        print("No images found for PDF.")
        return

    image_list = [Image.open(img).convert("RGB") for img in images]
    pdf_path = os.path.join(output_folder, pdf_filename)
    image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])
    print(f"PDF saved to: {pdf_path}")

    for img_path in images:
        os.remove(img_path)
    print("Temporary frames deleted.")
    
## ---Conpress PDF---
def compress_pdf(input_pdf, output_pdf, quality=75):
    from PyPDF2 import PdfReader, PdfWriter
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)
    
    print(f"Compressed PDF saved to: {output_pdf}")