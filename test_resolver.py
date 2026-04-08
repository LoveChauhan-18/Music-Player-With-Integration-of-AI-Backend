import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

# Mock Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.utils.youtube_resolver import resolve_youtube_audio

def test_resolver():
    query = "Arijit Singh - Chaleya official audio"
    print(f"Testing resolver with query: {query}")
    url = resolve_youtube_audio(query)
    if url:
        print(f"SUCCESS: Resolved URL: {url[:100]}...")
    else:
        print("FAILED: No URL resolved.")

if __name__ == "__main__":
    test_resolver()
