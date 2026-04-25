import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from core.models import Artist, Song
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Sync latest songs from iTunes API into the project database'

    def handle(self, *args, **options):
        self.stdout.write('Starting bulk song sync from iTunes API...')
        
        categories = [
            {'name': 'Bollywood', 'terms': ['bollywood hindi hits', 'latest arijit singh', 'bollywood romantic'], 'country': 'in'},
            {'name': 'Hollywood', 'terms': ['top pop hits', 'billboard hot 100', 'rnb hits'], 'country': 'us'},
            {'name': 'K-Pop', 'terms': ['koreap pop hits', 'bts hits', 'blackpink latest', 'new jeans'], 'country': 'kr'},
            {'name': 'J-Pop', 'terms': ['japanese pop', 'anime openings', 'city pop japan', 'jpop latest'], 'country': 'jp'},
        ]

        total_synced = 0
        for cat in categories:
            self.stdout.write(f"--- Fetching {cat['name']} ---")
            cat_synced = 0
            seen_track_ids = set()

            for term in cat['terms']:
                if cat_synced >= 200: break

                url = f"https://itunes.apple.com/search?term={term}&media=music&entity=song&limit=200&country={cat['country']}"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        results = response.json().get('results', [])
                        self.stdout.write(f"  Found {len(results)} results for '{term}'")
                        
                        for track in results:
                            if cat_synced >= 200: break
                            
                            track_id = track.get('trackId')
                            if track_id in seen_track_ids: continue
                            seen_track_ids.add(track_id)

                            artist_name = track.get('artistName', 'Unknown Artist')
                            track_name = track.get('trackName', 'Unknown Song')
                            preview_url = track.get('previewUrl')
                            artwork_url = track.get('artworkUrl100', '').replace('100x100', '600x600')
                            album_name = track.get('collectionName', 'Single')
                            genre_name = track.get('primaryGenreName', 'Music')
                            
                            if not preview_url: continue

                            # Get or create artist
                            artist, _ = Artist.objects.get_or_create(name=artist_name)

                            # Check if song exists by title and artist
                            song, created = Song.objects.get_or_create(
                                title=track_name, 
                                artist=artist,
                                defaults={
                                    'preview_url': preview_url,
                                    'artwork_url': artwork_url,
                                    'album': album_name,
                                    'genre': genre_name,
                                    'plays': track.get('trackCount', 0) * 1000 # dummy play count based on some itunes data or random
                                }
                            )

                            if created:
                                cat_synced += 1
                                total_synced += 1
                                if total_synced % 20 == 0:
                                    self.stdout.write(f"    Processed {total_synced} songs total...")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    Error syncing {term}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"Synced {cat_synced} songs for {cat['name']}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {total_synced} NEW songs across all categories!"))
