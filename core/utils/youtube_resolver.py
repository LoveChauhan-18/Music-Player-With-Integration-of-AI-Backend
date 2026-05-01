import urllib.request
import urllib.parse
import json
import subprocess
import ssl
import concurrent.futures


def resolve_youtube_audio(query):
    """
    Resolves a full audio stream URL for the given search query.
    Strategy:
    1. Try yt-dlp with Android/iOS YouTube clients (bypasses data-center IP blocks on Render).
    2. Fallback: JioSaavn API (only if URL is verified accessible from this server).
    3. Fallback: Piped API instances.
    """
    print(f"Resolving audio for: {query}")

    # ─── Attempt 1: yt-dlp with multiple client profiles ─────────────────────
    # Android/iOS clients avoid the JavaScript runtime requirement and often
    # bypass Render's data-center IP restrictions from YouTube.
    ytdlp_configs = [
        # Android client (most reliable bypass)
        ["yt-dlp", "--get-url", "--format", "bestaudio/best",
         "--extractor-args", "youtube:player_client=android",
         "--no-check-formats", "--no-warnings", "--quiet",
         f"ytsearch1:{query}"],
        # iOS client
        ["yt-dlp", "--get-url", "--format", "bestaudio/best",
         "--extractor-args", "youtube:player_client=ios",
         "--no-check-formats", "--no-warnings", "--quiet",
         f"ytsearch1:{query}"],
        # Default client (last resort)
        ["yt-dlp", "--get-url", "--format", "bestaudio",
         "--no-warnings", "--quiet",
         f"ytsearch1:{query}"],
    ]

    for cmd in ytdlp_configs:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                # yt-dlp can output multiple lines (one URL per format); take first valid one
                urls = [
                    line.strip()
                    for line in result.stdout.strip().split('\n')
                    if line.strip().startswith('http')
                ]
                if urls:
                    client = "android" if "android" in str(cmd) else ("ios" if "ios" in str(cmd) else "default")
                    print(f"Resolved via yt-dlp ({client} client)")
                    return urls[0]
        except subprocess.TimeoutExpired:
            print(f"yt-dlp timeout ({cmd})")
        except Exception as e:
            print(f"yt-dlp error: {e}")

    # ─── Attempt 2 & 3: JioSaavn + Piped concurrently ────────────────────────
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    saavn_instances = [
        "https://jiosaavn-api-v3.vercel.app",
        "https://saavn.dev/api",
        "https://jiosaavn-api-beta-three.vercel.app/api",
        "https://jiosaavn-api.vercel.app",
        "https://saavn.me",
    ]

    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.rivo.cc",
        "https://piped-api.lunar.icu",
        "https://api-piped.mha.fi",
        "https://pipedapi.darkness.services",
    ]

    def verify_url(url):
        """Returns True if the URL is actually accessible (not 404) from this server."""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.jiosaavn.com/',
            })
            req.get_method = lambda: 'HEAD'
            resp = urllib.request.urlopen(req, timeout=6)
            return resp.status < 400
        except Exception:
            return False

    def check_saavn(instance):
        try:
            search_query = urllib.parse.quote(query)

            # v3: /search → /song?id=
            try:
                req = urllib.request.Request(
                    f"{instance}/search?query={search_query}",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                results = data.get('data', {}).get('results') or data.get('results')
                if results:
                    song_id = results[0].get('id')
                    if song_id:
                        # Try /song?id= (v3 style — returns media_url directly)
                        try:
                            req2 = urllib.request.Request(
                                f"{instance}/song?id={song_id}",
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )
                            with urllib.request.urlopen(req2, timeout=5) as r2:
                                d2 = json.loads(r2.read().decode())
                                # Prefer 320kbps, then 160kbps
                                media_urls = d2.get('media_urls', {})
                                media = (
                                    media_urls.get('320_KBPS') or
                                    media_urls.get('160_KBPS') or
                                    d2.get('media_url')
                                )
                                if media and verify_url(media):
                                    return media
                        except Exception:
                            pass

                        # Try /songs?id= (v4 style — returns downloadUrl list)
                        try:
                            req3 = urllib.request.Request(
                                f"{instance}/songs?id={song_id}",
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )
                            with urllib.request.urlopen(req3, timeout=5) as r3:
                                d3 = json.loads(r3.read().decode())
                                track_results = d3.get('data') or d3.get('results')
                                if track_results:
                                    track = track_results[0] if isinstance(track_results, list) else track_results
                                    urls = track.get('downloadUrl') or track.get('download_url')
                                    if urls and isinstance(urls, list):
                                        for item in reversed(urls):  # highest quality last
                                            link = item.get('link') if isinstance(item, dict) else item
                                            if link and verify_url(link):
                                                return link
                        except Exception:
                            pass
            except Exception:
                pass

            # Fallback: /search/songs?query= (older v4 style)
            try:
                req4 = urllib.request.Request(
                    f"{instance}/search/songs?query={search_query}",
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req4, timeout=5) as r4:
                    d4 = json.loads(r4.read().decode())
                    results2 = d4.get('data', {}).get('results') or d4.get('results')
                    if results2:
                        track = results2[0]
                        urls = track.get('downloadUrl') or track.get('download_url')
                        if urls and isinstance(urls, list):
                            for item in reversed(urls):
                                link = item.get('link') if isinstance(item, dict) else item
                                if link and verify_url(link):
                                    return link
            except Exception:
                pass

        except Exception:
            pass
        return None

    def check_piped(instance):
        try:
            search_url = f"{instance}/search?q={urllib.parse.quote(query)}&filter=videos"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                search_data = json.loads(resp.read().decode())
                if search_data.get('items'):
                    video_url = search_data['items'][0].get('url', '')
                    video_id = video_url.split('v=')[-1] if '/watch?v=' in video_url else video_url.split('=')[-1]
                    if video_id:
                        with urllib.request.urlopen(
                            f"{instance}/streams/{video_id}", timeout=5, context=ctx
                        ) as stream_resp:
                            stream_data = json.loads(stream_resp.read().decode())
                            audio_streams = stream_data.get('audioStreams', [])
                            if audio_streams:
                                return audio_streams[0]['url']
        except Exception:
            pass
        return None

    print("Trying JioSaavn + Piped fallbacks concurrently...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        saavn_futures = {executor.submit(check_saavn, inst): inst for inst in saavn_instances}
        piped_futures = {executor.submit(check_piped, inst): inst for inst in piped_instances}
        all_futures = {**saavn_futures, **piped_futures}

        for future in concurrent.futures.as_completed(all_futures):
            try:
                url = future.result()
                if url:
                    source = "JioSaavn" if all_futures[future] in saavn_instances else "Piped"
                    print(f"Resolved via {source} ({all_futures[future]})")
                    return url
            except Exception:
                pass

    print("Failed to resolve full audio from all sources.")
    return None
