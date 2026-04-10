import urllib.request
import urllib.parse
import json

def resolve_youtube_audio(query):
    """
    Given a search query (e.g. "Artist - Title"), finds the best matching 
    audio stream URL. Now utilizes a reliable JioSaavn API to avoid 
    YouTube IP restrictions and 403 Forbidden errors on Render.
    """
    try:
        url = f"https://jiosaavn-api-privatecvc2.vercel.app/search/songs?query={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, timeout=8)
        data = json.loads(res.read())
        
        if data and data.get('data') and data['data'].get('results'):
            song = data['data']['results'][0]
            if 'downloadUrl' in song and isinstance(song['downloadUrl'], list):
                highest_quality = song['downloadUrl'][-1]
                return highest_quality.get('link') or highest_quality.get('url')
    except Exception as e:
        print(f"Error resolving full audio: {e}")
        
    return None
