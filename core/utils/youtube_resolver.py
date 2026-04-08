import yt_dlp
import os

def resolve_youtube_audio(query):
    """
    Given a search query (e.g. "Artist - Title"), finds the best matching 
    video on YouTube and returns a direct audio stream URL.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'max_downloads': 1,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_color': True,
        'extract_flat': False,
        'skip_download': True,
        'force_generic_extractor': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search for the query and extract info
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if not info or 'entries' not in info or not info['entries']:
                return None
            
            entry = info['entries'][0]
            # Get the best audio format URL
            return entry.get('url')
    except Exception as e:
        print(f"Error resolving YouTube audio: {e}")
        return None
