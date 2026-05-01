import urllib.request
import urllib.parse
import json
import subprocess
import ssl
import concurrent.futures
import time

def resolve_youtube_audio(query):
    """
    Resolves a full audio stream URL for the given search query.
    Uses concurrency to race yt-dlp against fallback APIs to minimize response time.
    """
    print(f"🔍 Resolving audio for: {query}")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    def run_ytdlp(client="android"):
        """Runs yt-dlp with a specific client profile."""
        cmd = ["yt-dlp", "--get-url", "--format", "bestaudio/best", "--no-warnings", "--quiet", "--no-check-formats"]
        if client == "android":
            cmd += ["--extractor-args", "youtube:player_client=android"]
        elif client == "ios":
            cmd += ["--extractor-args", "youtube:player_client=ios"]
        
        cmd += [f"ytsearch1:{query}"]
        
        try:
            # We use a strict timeout here to prevent gunicorn worker kills
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=18)
            if result.returncode == 0:
                urls = [l.strip() for l in result.stdout.split('\n') if l.strip().startswith('http')]
                if urls:
                    print(f"✅ Resolved via yt-dlp ({client})")
                    return urls[0]
        except Exception:
            pass
        return None

    def verify_url(url):
        """Minimal HEAD request to check if URL is alive."""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.jiosaavn.com/'})
            req.get_method = lambda: 'HEAD'
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status < 400
        except:
            return False

    def check_saavn(instance):
        try:
            q = urllib.parse.quote(query)
            # Try search v3
            with urllib.request.urlopen(f"{instance}/search?query={q}", timeout=4) as r:
                data = json.loads(r.read().decode())
            results = data.get('data', {}).get('results') or data.get('results')
            if results:
                sid = results[0].get('id')
                if sid:
                    # Try /song?id=
                    with urllib.request.urlopen(f"{instance}/song?id={sid}", timeout=4) as r2:
                        d2 = json.loads(r2.read().decode())
                        urls = d2.get('media_urls', {})
                        media = urls.get('320_KBPS') or urls.get('160_KBPS') or d2.get('media_url')
                        if media and verify_url(media):
                            print(f"✅ Resolved via JioSaavn ({instance})")
                            return media
        except: pass
        return None

    def check_piped(instance):
        try:
            q = urllib.parse.quote(query)
            with urllib.request.urlopen(f"{instance}/search?q={q}&filter=videos", timeout=4, context=ctx) as r:
                data = json.loads(r.read().decode())
            if data.get('items'):
                url = data['items'][0].get('url', '')
                vid = url.split('v=')[-1] if 'v=' in url else url.split('=')[-1]
                if vid:
                    with urllib.request.urlopen(f"{instance}/streams/{vid}", timeout=4, context=ctx) as r2:
                        d2 = json.loads(r2.read().decode())
                        streams = d2.get('audioStreams', [])
                        if streams:
                            print(f"✅ Resolved via Piped ({instance})")
                            return streams[0]['url']
        except: pass
        return None

    # Race them all!
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # 1. Start yt-dlp android (best quality)
        futures = {executor.submit(run_ytdlp, "android"): "ytdlp_android"}
        
        # 2. Start fallbacks (fastest)
        saavn_instances = ["https://jiosaavn-api-v3.vercel.app", "https://saavn.dev/api", "https://saavn.me"]
        piped_instances = ["https://pipedapi.kavin.rocks", "https://pipedapi.rivo.cc", "https://api-piped.mha.fi"]
        
        for inst in saavn_instances:
            futures[executor.submit(check_saavn, inst)] = f"saavn_{inst}"
        for inst in piped_instances:
            futures[executor.submit(check_piped, inst)] = f"piped_{inst}"

        # Get the first one that returns a valid URL
        # We wait up to 25s total (staying under 30s gunicorn limit)
        start_time = time.time()
        for future in concurrent.futures.as_completed(futures, timeout=24):
            try:
                url = future.result()
                if url:
                    # Cancel other tasks (they'll keep running but we don't care)
                    return url
            except:
                pass
            if time.time() - start_time > 24:
                break

    print("❌ All resolution attempts failed or timed out.")
    return None
