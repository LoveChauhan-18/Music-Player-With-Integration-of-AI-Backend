import urllib.request
import urllib.parse
import json
import subprocess
import ssl
import time
import concurrent.futures

def resolve_youtube_audio(query):
    """
    Given a search query (e.g. "Artist - Title"), finds the best matching 
    audio stream URL. Utilizes an expanded set of Piped API instances 
    and a reliable JioSaavn API fallback concurrently to avoid timeouts.
    """
    print(f"🔍 Resolving audio for: {query}")

    # Attempt 1: yt-dlp (Best quality, but often blocked on Render)
    try:
        cmd = [
            "yt-dlp",
            "--get-url",
            "--format", "bestaudio",
            f"ytsearch1:{query}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        
        if result.returncode == 0:
            url = result.stdout.strip()
            if url and "googlevideo.com" in url:
                print("✅ Resolved via yt-dlp")
                return url
        else:
            print(f"⚠️ yt-dlp failed with return code {result.returncode}")
    except Exception as e:
        print(f"❌ yt-dlp resolution error: {e}")

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

    saavn_instances = [
        "https://saavn.dev/api",
        "https://jiosaavn-api-beta-three.vercel.app/api",
        "https://jiosaavn-api-v3.vercel.app",
        "https://saavn.me",
        "https://jiosaavn-api.vercel.app"
    ]

    def check_piped(instance):
        try:
            search_url = f"{instance}/search?q={urllib.parse.quote(query)}&filter=videos"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                search_data = json.loads(response.read().decode())
                if search_data.get('items'):
                    video_url = search_data['items'][0].get('url', '')
                    video_id = video_url.split('v=')[-1] if '/watch?v=' in video_url else video_url.split('=')[-1]
                    if video_id:
                        stream_url = f"{instance}/streams/{video_id}"
                        with urllib.request.urlopen(stream_url, timeout=5, context=ctx) as stream_resp:
                            stream_data = json.loads(stream_resp.read().decode())
                            audio_streams = stream_data.get('audioStreams', [])
                            if audio_streams:
                                return audio_streams[0]['url']
        except Exception:
            pass
        return None

    def check_saavn(instance):
        try:
            search_query = urllib.parse.quote(query)
            # Try v3 search style
            search_url = f"{instance}/search?query={search_query}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                results = data.get('data', {}).get('results') or data.get('results')
                if results and len(results) > 0:
                    song_id = results[0].get('id')
                    if song_id:
                        # Try /song?id= (v3)
                        try:
                            details_url = f"{instance}/song?id={song_id}"
                            req_details = urllib.request.Request(details_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req_details, timeout=5) as resp_details:
                                details_data = json.loads(resp_details.read().decode())
                                media = details_data.get('media_url') or details_data.get('download_url')
                                if media:
                                    if isinstance(media, list) and len(media) > 0:
                                        best = media[-1]
                                        return best.get('link') if isinstance(best, dict) else best
                                    elif isinstance(media, str):
                                        return media
                        except Exception:
                            pass
                        
                        # Try /songs?id= (v4)
                        try:
                            details_url = f"{instance}/songs?id={song_id}"
                            req_details = urllib.request.Request(details_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req_details, timeout=5) as resp_details:
                                details_data = json.loads(resp_details.read().decode())
                                track_results = details_data.get('data') or details_data.get('results')
                                if track_results:
                                    track = track_results[0] if isinstance(track_results, list) else track_results
                                    urls = track.get('downloadUrl') or track.get('download_url')
                                    if urls and isinstance(urls, list) and len(urls) > 0:
                                        best = urls[-1]
                                        return best.get('link') if isinstance(best, dict) else best
                        except Exception:
                            pass

            # Fallback to direct /search/songs?query= (older v4)
            search_url_2 = f"{instance}/search/songs?query={search_query}"
            req2 = urllib.request.Request(search_url_2, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=5) as response2:
                data2 = json.loads(response2.read().decode())
                results2 = data2.get('data', {}).get('results') or data2.get('results')
                if results2 and len(results2) > 0:
                    track = results2[0]
                    urls = track.get('downloadUrl') or track.get('download_url')
                    if urls and isinstance(urls, list) and len(urls) > 0:
                        best = urls[-1]
                        return best.get('link') if isinstance(best, dict) else best

        except Exception:
            pass
        return None

    print("📡 Trying Piped and JioSaavn fallbacks concurrently...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Submit all Piped requests
        piped_futures = {executor.submit(check_piped, inst): inst for inst in piped_instances}
        # Submit all JioSaavn requests
        saavn_futures = {executor.submit(check_saavn, inst): inst for inst in saavn_instances}
        
        # Combine all futures
        all_futures = {**piped_futures, **saavn_futures}
        
        for future in concurrent.futures.as_completed(all_futures):
            instance = all_futures[future]
            try:
                url = future.result()
                if url:
                    source = "Piped" if instance in piped_instances else "JioSaavn"
                    print(f"✅ Resolved via {source} ({instance})")
                    # Cancel remaining tasks by shutting down executor early for this context
                    # Though python threads can't be easily cancelled, we can just return early
                    return url
            except Exception as e:
                pass

    print("❌ Failed to resolve full audio from all sources.")
    return None

