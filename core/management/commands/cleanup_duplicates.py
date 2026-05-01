from django.core.management.base import BaseCommand
from core.models import Song, Artist
from django.db.models import Count

class Command(BaseCommand):
    help = 'Identifies and removes duplicate songs based on Title and Artist'

    def handle(self, *args, **options):
        self.stdout.write('Scanning for duplicate artists...')
        artist_dups = Artist.objects.values('name').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        artist_removed = 0
        for dup in artist_dups:
            name = dup['name']
            matches = list(Artist.objects.filter(name=name).order_by('id'))
            keep = matches[0]
            to_delete = matches[1:]
            
            for d in to_delete:
                # Move all songs to the kept artist
                Song.objects.filter(artist=d).update(artist=keep)
                d.delete()
                artist_removed += 1
        
        self.stdout.write(self.style.SUCCESS(f"Cleaned up {artist_removed} duplicate artists."))

        self.stdout.write('Scanning for duplicate songs...')
        
        # Find duplicates by Title and Artist
        duplicates = Song.objects.values('title', 'artist').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_removed = 0
        total_found = duplicates.count()
        
        if total_found == 0:
            self.stdout.write(self.style.SUCCESS("No duplicate songs found!"))
            return

        self.stdout.write(f"Processing {total_found} groups of duplicates...")
        
        for dup in duplicates:
            title = dup['title']
            artist_id = dup['artist']
            
            # Fetch all matching songs
            matches = list(Song.objects.filter(title=title, artist_id=artist_id).order_by('-external_id', 'created_at'))
            
            # Keep the first one
            keep = matches[0]
            to_delete = matches[1:]
            
            for d in to_delete:
                # Reassign playlist relations
                for ps in d.song_playlists.all():
                    if not ps.playlist.playlist_songs.filter(song=keep).exists():
                        ps.song = keep
                        ps.save()
                    else:
                        ps.delete()
                
                d.delete()
                total_removed += 1
                
        self.stdout.write(self.style.SUCCESS(f"Cleanup complete! Removed {total_removed} duplicate records."))
