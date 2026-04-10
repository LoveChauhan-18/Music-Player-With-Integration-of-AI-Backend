import yt_dlp
import os
import concurrent.futures

def fetch_youtube_podcasts():
    """
    Fetches famous Indian podcasts from YouTube using yt-dlp.
    Returns a list of podcast metadata objects.
    """
    queries = [
        "The Ranveer Show (BeerBiceps)",
        "Raj Shamani Figuring Out podcast",
        "Dostcast latest",
        "Prakhar ke Pravachan podcast",
        "The Seen and the Unseen podcast",
        "Cyrus Says podcast latest",
        "Famous Indian Podcasts 2026",
        "Ranveer Show Hindi clips",
    ]

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    all_podcasts = []
    seen_ids = set()

    def search_query(q):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for 20 results per query to ensure diversity and reach 100+ total
                info = ydl.extract_info(f"ytsearch20:{q}", download=False)
                if not info or 'entries' not in info:
                    return []
                return info['entries']
        except Exception as e:
            print(f"Error searching for {q}: {e}")
            return []

    # Use ThreadPoolExecutor for faster concurrent fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(search_query, queries))

    for entry_list in results:
        for entry in entry_list:
            if not entry or entry.get('id') in seen_ids:
                continue
            
            seen_ids.add(entry.get('id'))
            
            # Normalize internal metadata
            podcast = {
                'id': entry.get('id'),
                'title': entry.get('title'),
                'artist': entry.get('uploader') or entry.get('channel') or "Unknown Channel",
                # hqdefault is the reliable standard
                'artwork': f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg",
                'duration': entry.get('duration') or 0,
                'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                'views': entry.get('view_count') or 0,
                'publishedAt': entry.get('upload_date') or "2026-04-09",
                'source': 'youtube'
            }
            all_podcasts.append(podcast)

    # Sort by views or most recent? Let's keep them somewhat shuffled or sorted by query
    return all_podcasts[:150] # Limit to 150 for performance
