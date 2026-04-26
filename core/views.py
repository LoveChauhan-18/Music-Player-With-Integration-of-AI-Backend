from django.contrib.auth import get_user_model
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()
from .serializers import RegisterSerializer, SongSerializer, PlaylistSerializer
from .models import Song
from .models import Playlist, PlaylistSong
from .serializers import PlaylistSongSerializer



@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Audit hint: List all environment variable keys (names only)
            import os
            keys = sorted(os.environ.keys())
            db_vars = [k for k in keys if 'DB' in k or 'DATABASE' in k or 'POSTGRES' in k or 'URL' in k]
            audit_msg = f"[Audit Keys: {', '.join(db_vars)}]" if db_vars else "[Audit: No DB keys found]"
            return Response({"error": f"{audit_msg} {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SongListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        try:
            query = request.GET.get('search')

            if query:
                songs = Song.objects.filter(title__icontains=query)
            else:
                songs = Song.objects.all()

            serializer = SongSerializer(songs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = SongSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SongDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return Song.objects.get(pk=pk)

    def get(self, request, pk):
        song = self.get_object(pk)
        serializer = SongSerializer(song)
        return Response(serializer.data)

    def put(self, request, pk):
        song = self.get_object(pk)
        serializer = SongSerializer(song, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        song = self.get_object(pk)
        song.delete()
        return Response({"message": "Deleted successfully"})
    

class PlaylistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Auto-initialize default playlists for the user if they don't exist
        default_playlists = ["Favourites", "Workout Mix", "Chill Vibes", "Late Night Focus"]
        for pl_name in default_playlists:
            Playlist.objects.get_or_create(user=request.user, name=pl_name)

        playlists = Playlist.objects.filter(user=request.user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PlaylistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.core.management import call_command


class AddSongToPlaylistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        playlist_id = request.data.get('playlist')
        song_id = request.data.get('song')
        song_metadata = request.data.get('song_metadata')

        if not playlist_id or not song_id:
            return Response({"error": "playlist and song are required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Verify playlist belongs to user
        playlist = Playlist.objects.filter(id=playlist_id, user=request.user).first()
        if not playlist:
            return Response({"error": "Playlist not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Resolve song_id to an integer safely
        try:
            song_id_int = int(song_id)
        except (ValueError, TypeError):
            song_id_int = None

        # 3. Try to find by DB id (local songs have small IDs < 1,000,000)
        song = None
        if song_id_int is not None and song_id_int < 1_000_000:
            song = Song.objects.filter(id=song_id_int).first()

        # 4. Try by external_id (covers iTunes and previously synced songs)
        if not song:
            song = Song.objects.filter(external_id=str(song_id)).first()

        # 5. Create the song if metadata is provided (use get_or_create to avoid unique violations)
        if not song and song_metadata:
            from .models import Artist
            artist_name = song_metadata.get('artist', 'Unknown Artist')
            # artist may be a nested dict for some song types
            if isinstance(artist_name, dict):
                artist_name = artist_name.get('name', 'Unknown Artist')
            artist, _ = Artist.objects.get_or_create(name=artist_name)

            song, _ = Song.objects.get_or_create(
                external_id=str(song_id),
                defaults={
                    'title': song_metadata.get('title', 'Untitled'),
                    'artist': artist,
                    'source': song_metadata.get('source', 'itunes'),
                    # frontend may send previewUrl (iTunes) or preview_url (local)
                    'preview_url': song_metadata.get('previewUrl') or song_metadata.get('preview_url'),
                    # frontend may send artwork (iTunes) or artwork_url (local)
                    'artwork_url': song_metadata.get('artwork') or song_metadata.get('artwork_url'),
                    'album': song_metadata.get('album'),
                    'genre': song_metadata.get('genre'),
                }
            )

        if not song:
            return Response({"error": "Song not found and no metadata provided for sync."}, status=status.HTTP_404_NOT_FOUND)

        # 6. Add to playlist (idempotent)
        if PlaylistSong.objects.filter(playlist=playlist, song=song).exists():
            return Response({"message": "Song already in playlist"}, status=status.HTTP_200_OK)

        PlaylistSong.objects.create(playlist=playlist, song=song)
        return Response({"message": "Song added to playlist"}, status=status.HTTP_201_CREATED)


class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        song_id = request.data.get('song_id')
        song_metadata = request.data.get('song_metadata')  # Optional metadata for external songs

        if not song_id:
            return Response({"error": "song_id is required"}, status=400)

        # 1. Resolve song_id to an integer safely
        try:
            song_id_int = int(song_id)
        except (ValueError, TypeError):
            song_id_int = None

        # 2. Try to find by DB id then by external_id
        song = None
        if song_id_int is not None and song_id_int < 1_000_000:
            song = Song.objects.filter(id=song_id_int).first()

        if not song:
            song = Song.objects.filter(external_id=str(song_id)).first()

        # 3. If not found and metadata provided, get or create it
        if not song and song_metadata:
            from .models import Artist
            artist_name = song_metadata.get('artist', 'Unknown Artist')
            if isinstance(artist_name, dict):
                artist_name = artist_name.get('name', 'Unknown Artist')
            artist, _ = Artist.objects.get_or_create(name=artist_name)

            song, _ = Song.objects.get_or_create(
                external_id=str(song_id),
                defaults={
                    'title': song_metadata.get('title', 'Untitled'),
                    'artist': artist,
                    'source': song_metadata.get('source', 'itunes'),
                    'preview_url': song_metadata.get('previewUrl') or song_metadata.get('preview_url'),
                    'artwork_url': song_metadata.get('artwork') or song_metadata.get('artwork_url'),
                    'album': song_metadata.get('album'),
                    'genre': song_metadata.get('genre'),
                }
            )

        if not song:
            return Response({"error": "Song not found and no metadata provided for sync."}, status=404)

        # 4. Toggle Like
        playlist, _ = Playlist.objects.get_or_create(
            user=request.user,
            name="Liked Songs"
        )
        liked_song = PlaylistSong.objects.filter(playlist=playlist, song=song).first()

        if liked_song:
            liked_song.delete()
            return Response({"liked": False, "message": "Removed from Liked Songs", "song_id": song.id})
        else:
            PlaylistSong.objects.create(playlist=playlist, song=song)
            return Response({"liked": True, "message": "Added to Liked Songs", "song_id": song.id})


class UserLikedSongsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        playlist, _ = Playlist.objects.get_or_create(
            user=request.user, 
            name="Liked Songs"
        )
        song_ids = list(playlist.playlist_songs.values_list('song_id', flat=True))
        return Response(song_ids)


import threading

class SyncLatestSongsView(APIView):
    permission_classes = [AllowAny] # Allow for demo/automation

    def post(self, request):
        def run_sync():
            try:
                from django.core.management import call_command
                call_command('sync_latest_songs')
            except Exception as e:
                print(f"Background sync error: {e}")

        # Start sync in a background thread to avoid request timeout
        threading.Thread(target=run_sync).start()
        
        return Response({
            "status": "success", 
            "message": "Sync started in background! Your library will update shortly."
        })


from .utils.youtube_resolver import resolve_youtube_audio
from .utils.podcast_fetcher import fetch_youtube_podcasts
from .utils.cartoon_fetcher import fetch_youtube_cartoons
from .utils.anime_fetcher import fetch_youtube_anime

class PodcastListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            podcasts = fetch_youtube_podcasts()
            return Response(podcasts)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class CartoonListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            cartoons = fetch_youtube_cartoons()
            return Response(cartoons)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class AnimeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            anime = fetch_youtube_anime()
            return Response(anime)
        except Exception as e:
            return Response({"error": str(e)}, status=500)



class ResolveAudioView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        title = request.data.get('title')
        artist = request.data.get('artist')
        
        if not title or not artist:
            return Response({"error": "title and artist are required"}, status=400)
        
        # Attempt 1: Artist + Title (Best match)
        query = f"{artist} {title}"
        audio_url = resolve_youtube_audio(query)
        
        # Attempt 2: Just Title (Fallback for misspelled artists)
        if not audio_url:
            audio_url = resolve_youtube_audio(title)

        if audio_url:
            return Response({"audio_url": audio_url})
        else:
            return Response({"error": "Could not resolve full audio"}, status=404)


class SelfCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        import os
        report = {
            "database": "unknown",
            "migrations": "unknown",
            "song_count": 0,
            "artist_count": 0,
            "resolver_test": "unknown",
            "env_keys": [k for k in os.environ.keys() if any(x in k for x in ['DB', 'DATABASE', 'POSTGRES', 'URL'])]
        }

        # Check DB
        try:
            from django.db import connection
            connection.ensure_connection()
            report["database"] = "connected"
        except Exception as e:
            report["database"] = f"error: {str(e)}"

        # Check Models & Counts
        try:
            from core.models import Song, Artist
            report["song_count"] = Song.objects.count()
            report["artist_count"] = Artist.objects.count()
            report["migrations"] = "applied"
        except Exception as e:
            report["migrations"] = f"error: {str(e)}"

        # Check Resolver
        try:
            test_url = resolve_youtube_audio("Blinding Lights")
            report["resolver_test"] = "working" if test_url else "failed (no URL returned)"
            if test_url:
                report["sample_url"] = test_url[:50] + "..."
        except Exception as e:
            report["resolver_test"] = f"error: {str(e)}"

        return Response(report)


class RedeployView(APIView):
    """Endpoint used to trigger a process exit so Render restarts the service.
    Call with a POST request. No auth required - keep the URL secret.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Immediately exit the worker process; Render will start a fresh container.
        import sys
        sys.exit(0)
        # Unreachable response kept for type checkers
        return Response({"status": "restarting"})
            