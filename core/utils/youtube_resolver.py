import urllib.request
import urllib.parse
import json

def resolve_youtube_audio(query):
    """
    Given a search query (e.g. "Artist - Title"), finds the best matching 
    audio stream URL. Now utilizes a reliable JioSaavn API fallback to avoid 
    YouTube IP restrictions and 403 Forbidden errors on Render.
    """
    import subprocess
    import urllib.request
    import urllib.parse
    import json

    # Attempt 1: yt-dlp (Best quality, but often blocked on Render)
    try:
        cmd = [
            "yt-dlp",
            "--get-url",
            "--format", "bestaudio",
            f"ytsearch1:{query}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        
        if result.returncode == 0:
            url = result.stdout.strip()
            if url and "googlevideo.com" in url:
                return url
    except Exception as e:
        print(f"yt-dlp resolution error: {e}")

    # Attempt 2: JioSaavn Unofficial API (Reliable fallback for Render)
    try:
        # Search for the song
        search_query = urllib.parse.quote(query)
        # Using a reliable public instance of the JioSaavn API
        search_url = f"https://saavn.me/search/songs?query={search_query}"
        
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 'SUCCESS' and data.get('data', {}).get('results'):
                # Get the first result
                track = data['data']['results'][0]
                download_urls = track.get('downloadUrl', [])
                if download_urls:
                    # Return the 320kbps link (usually the last one)
                    return download_urls[-1]['link']
    except Exception as e:
        print(f"JioSaavn resolution error: {e}")
        
    return None
