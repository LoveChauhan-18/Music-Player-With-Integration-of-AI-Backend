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

    # Attempt 2: Piped API (Highly reliable fallback)
    try:
        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://api.piped.victr.me",
            "https://pipedapi.darkness.services"
        ]
        for instance in piped_instances:
            search_url = f"{instance}/search?q={urllib.parse.quote(query)}&filter=videos"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                search_data = json.loads(response.read().decode())
                if search_data.get('items'):
                    video_id = search_data['items'][0].get('url', '').split('=')[-1]
                    # Now get streams for this video
                    stream_url = f"{instance}/streams/{video_id}"
                    with urllib.request.urlopen(stream_url, timeout=5) as stream_resp:
                        stream_data = json.loads(stream_resp.read().decode())
                        # Find best audio stream
                        audio_streams = stream_data.get('audioStreams', [])
                        if audio_streams:
                            return audio_streams[0]['url']
    except Exception as e:
        print(f"Piped resolution error: {e}")

    # Attempt 3: JioSaavn Unofficial API (Final fallback)
    saavn_instances = [
        "https://saavn.me",
        "https://jiosaavn-api-v3.vercel.app",
        "https://jiosaavn-api.vercel.app"
    ]
    
    for instance in saavn_instances:
        try:
            search_query = urllib.parse.quote(query)
            search_url = f"{instance}/search/songs?query={search_query}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('status') == 'SUCCESS' and data.get('data', {}).get('results'):
                    track = data['data']['results'][0]
                    download_urls = track.get('downloadUrl', [])
                    if download_urls:
                        return download_urls[-1]['link']
        except:
            continue
        
    return None
