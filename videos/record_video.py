from playwright.sync_api import sync_playwright
import time
import subprocess
import os

# Paths
html_file = r"C:\Users\Alexander\Documents\GitHub\ai-coding-agents-industry-analysis\videos\video-06-minimalist-apple-full.html"
output_video = r"C:\Users\Alexander\Documents\GitHub\ai-coding-agents-industry-analysis\videos\ai-coding-agents-video.webm"
final_video = r"C:\Users\Alexander\Documents\GitHub\ai-coding-agents-industry-analysis\videos\ai-coding-agents-video.mp4"
audio_file = r"C:\Users\Alexander\Documents\GitHub\ai-coding-agents-industry-analysis\videos\soundtrack.mp3"
ffmpeg_path = r"C:\Users\Alexander\Downloads\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"

# Calculate total duration from HTML (in ms)
# Slides: 4500 + 5000 + 4500 + 5500 + 5500 + 5500 + 5500 + 4500 + 4000 + 4500 = 49000ms
total_duration_ms = 49000 + 2000  # Add 2 seconds buffer for final slide
total_duration_sec = total_duration_ms / 1000

print(f"Recording video for {total_duration_sec} seconds...")

with sync_playwright() as p:
    # Launch browser with video recording
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1080, "height": 1080},
        record_video_dir=".",
        record_video_size={"width": 1080, "height": 1080}
    )

    page = context.new_page()

    # Navigate to the HTML file
    page.goto(f"file:///{html_file}")

    # Wait for the presentation to complete
    print("Recording presentation...")
    time.sleep(total_duration_sec)

    # Close to save the video
    page.close()
    context.close()
    browser.close()

    # Get the recorded video path
    video_path = page.video.path()
    print(f"Video recorded: {video_path}")

    # Move to output location
    os.rename(video_path, output_video)
    print(f"Video saved to: {output_video}")

# Combine video with audio using FFmpeg
print("Adding audio track...")
cmd = [
    ffmpeg_path,
    "-y",  # Overwrite output
    "-i", output_video,  # Input video
    "-i", audio_file,  # Input audio
    "-c:v", "libx264",  # Video codec
    "-c:a", "aac",  # Audio codec
    "-shortest",  # Cut to shortest stream
    "-pix_fmt", "yuv420p",  # Pixel format for compatibility
    final_video
]

subprocess.run(cmd, check=True)
print(f"\nDone! Video saved to: {final_video}")
