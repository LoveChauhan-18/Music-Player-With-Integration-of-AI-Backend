import yt_dlp
import concurrent.futures

def fetch_youtube_anime():
    """
    Fetches famous anime from YouTube and groups them by series.
    Returns: [{'series': 'Title', 'episodes': [...]}, ...]
    """
    series_list = [
        "Naruto Full Episodes",
        "Dragon Ball Z Full Episodes",
        "One Piece Episodes",
        "Death Note Episodes",
        "Jujutsu Kaisen Episodes",
        "Demon Slayer Full Episodes",
        "Pokemon Hindi Episodes",
        "Attack on Titan Episodes"
    ]

    # Custom premium artwork mapping
    ARTWORK_MAP = {
        "Dragon Ball Z": "/images/dbz.png",
        "Death Note": "/images/deathnote.jpg", # Local high-quality poster
    }

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    def fetch_series(series_query):
        # Display name for the series (cleaned up query)
        series_name = series_query.replace(" Full Episodes", "").replace(" Episodes", "").replace(" Hindi", "")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for 300 results per series to capture a more complete list of episodes
                info = ydl.extract_info(f"ytsearch300:{series_query}", download=False)
                if not info or 'entries' not in info:
                    return None
                
                episodes = []
                for entry in info['entries']:
                    if not entry: continue
                    
                    # Filter: Favor actual episodes or good compilations ( > 5 mins )
                    duration = entry.get('duration') or 0
                    if duration > 0 and duration < 300:
                        continue
                        
                    episodes.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        # Try maxres, fallback to hqdefault (standard YT thumbnail logic)
                        'artwork': f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg",
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

    return [r for r in results if r]
