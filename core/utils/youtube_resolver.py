import urllib.request
import urllib.parse
import json

def resolve_youtube_audio(query):
    """
    Given a search query (e.g. "Artist - Title"), finds the best matching 
    audio stream URL. Now utilizes an expanded set of Piped API instances 
    and a reliable JioSaavn API fallback to avoid YouTube IP restrictions.
    """
    import subprocess
    import urllib.request
    import urllib.parse
    import json
    import ssl
    import time

    print(f"🔍 Resolving audio for: {query}")

    # Attempt 1: yt-dlp (Best quality, but often blocked on Render)
    try:
        cmd = [
            "yt-dlp",
            "--get-url",
            "--format", "bestaudio",
            f"ytsearch1:{query}"
        ]
        # Shorter timeout for yt-dlp to fail fast and move to fallbacks
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            url = result.stdout.strip()
            if url and "googlevideo.com" in url:
                print("✅ Resolved via yt-dlp")
                return url
        else:
            print(f"⚠️ yt-dlp failed with return code {result.returncode}")
    except Exception as e:
        print(f"❌ yt-dlp resolution error: {e}")

    # Attempt 2: Piped API (Highly reliable fallback)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        piped_instances = [
            "https://pipedapi.kavin.rocks",
            "https://api.piped.victr.me",
            "https://pipedapi.darkness.services",
            "https://pipedapi.rivo.cc",
            "https://piped-api.lunar.icu",
            "https://api-piped.mha.fi",
            "https://pipedapi.official-halal.workers.dev"
        ]
        
        for instance in piped_instances:
            try:
                print(f"📡 Trying Piped instance: {instance}")
                search_url = f"{instance}/search?q={urllib.parse.quote(query)}&filter=videos"
                req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
                
                with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
                    search_data = json.loads(response.read().decode())
                    if search_data.get('items'):
                        video_id = search_data['items'][0].get('url', '').split('=')[-1]
                        if not video_id:
                            # Handle different URL formats if necessary
                            video_url = search_data['items'][0].get('url', '')
                            if '/watch?v=' in video_url:
                                video_id = video_url.split('v=')[-1]
                        
                        if video_id:
                            # Now get streams for this video
                            stream_url = f"{instance}/streams/{video_id}"
                            with urllib.request.urlopen(stream_url, timeout=6, context=ctx) as stream_resp:
                                stream_data = json.loads(stream_resp.read().decode())
                                audio_streams = stream_data.get('audioStreams', [])
                                if audio_streams:
                                    print(f"✅ Resolved via Piped ({instance})")
                                    return audio_streams[0]['url']
            except Exception as e:
                print(f"⚠️ Piped instance {instance} failed: {e}")
                continue
    except Exception as e:
        print(f"❌ Piped resolution master error: {e}")

    # Attempt 3: JioSaavn Unofficial API (Final fallback)
    print("📡 Trying JioSaavn fallback...")
    saavn_instances = [
        "https://saavn.me",
        "https://jiosaavn-api-v3.vercel.app",
        "https://jiosaavn-api.vercel.app",
        "https://jiosaavn-api-beta.vercel.app"
    ]
    
    for instance in saavn_instances:
        try:
            search_query = urllib.parse.quote(query)
            search_url = f"{instance}/search/songs?query={search_query}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                data = json.loads(response.read().decode())
                # Some APIs return different structures
                results = data.get('data', {}).get('results') or data.get('results')
                if results:
                    track = results[0]
                    download_urls = track.get('downloadUrl') or track.get('download_url')
                    if download_urls:
                        # Return the highest quality link (usually the last one)
                        print(f"✅ Resolved via JioSaavn ({instance})")
                        return download_urls[-1]['link'] if isinstance(download_urls[-1], dict) else download_urls[-1]
        except Exception as e:
            print(f"⚠️ JioSaavn instance {instance} failed: {e}")
            continue
        
    print("❌ Failed to resolve full audio from all sources.")
    return None
