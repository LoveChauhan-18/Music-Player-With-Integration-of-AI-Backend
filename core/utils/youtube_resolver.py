import urllib.request
import urllib.parse
import json

def resolve_youtube_audio(query):
    """
    Given a search query (e.g. "Artist - Title"), finds the best matching 
    audio stream URL. Now utilizes a reliable JioSaavn API to avoid 
    YouTube IP restrictions and 403 Forbidden errors on Render.
    """
    import subprocess
    try:
        # Use yt-dlp to find the best audio-only stream URL from YouTube
        # This is the most reliable way to get the FULL song
        cmd = [
            "yt-dlp",
            "--get-url",
            "--format", "bestaudio",
            f"ytsearch1:{query}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            url = result.stdout.strip()
            if url:
                return url
    except Exception as e:
        print(f"yt-dlp resolution error: {e}")
        
    return None
