import yt_dlp
import concurrent.futures

def fetch_youtube_cartoons():
    """
    Fetches famous cartoons from YouTube and groups them by series.
    Returns: [{'series': 'Title', 'episodes': [...]}, ...]
    """
    series_list = [
        "Tom and Jerry",
        "Oggy and the Cockroaches",
        "Ben 10",
        "Doraemon",
        "Shin Chan",
        "Mr Bean Cartoon",
        "Motu Patlu",
        "Ninja Hattori",
        "Pakdam Pakdai",
        "Chhota Bheem",
        "Roll No 21",
        "Peppa Pig",
        "Shaun the Sheep",
        "Grizzy & the Lemmings"
    ]

    # Custom premium artwork mapping
    ARTWORK_MAP = {
        "Doraemon": "/images/doraemon.png",
        "Shin Chan": "/images/shinchan.png",
        "Ninja Hattori": "/images/ninja_hattori.png",
        "Chhota Bheem": "/images/chhota_bheem.png",
        "Peppa Pig": "/images/peppa_pig.png",
    }

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    def fetch_series(series_name):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for 200 results per series to ensure ~100+ complete episodes after filtering
                info = ydl.extract_info(f"ytsearch200:{series_name} full episodes", download=False)
                if not info or 'entries' not in info:
                    return None
                
                episodes = []
                for entry in info['entries']:
                    if not entry: continue
                    
                    # Filter: Skip short clips/trailers (less than 5 mins)
                    duration = entry.get('duration') or 0
                    if duration > 0 and duration < 300:
                        continue

                    episodes.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        # Ensure every episode has a high-quality thumbnail
                        'artwork': f"https://i.ytimg.com/vi/{entry.get('id')}/maxresdefault.jpg",
                        'duration': duration,
                    })
                
                # Use custom artwork if mapped, otherwise use first episode's thumb
                custom_artwork = ARTWORK_MAP.get(series_name)
                
                return {
                    'series': series_name,
                    'artwork': custom_artwork if custom_artwork else (episodes[0]['artwork'] if episodes else None),
                    'episodes': episodes
                }
        except Exception as e:
            print(f"Error fetching {series_name}: {e}")
            return None

    # Fetch all series concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(fetch_series, series_list))

    # Filter out None results
    return [r for r in results if r]
