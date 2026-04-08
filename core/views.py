from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

User = get_user_model()
from .serializers import RegisterSerializer, SongSerializer
from .models import Song
from .models import Playlist, PlaylistSong
from .serializers import PlaylistSerializer, PlaylistSongSerializer



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"})
        return Response(serializer.errors)



class SongListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        query = request.GET.get('search')

        if query:
            songs = Song.objects.filter(title__icontains=query)
        else:
            songs = Song.objects.all()

        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SongSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)



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
        return Response(serializer.errors)

    def delete(self, request, pk):
        song = self.get_object(pk)
        song.delete()
        return Response({"message": "Deleted successfully"})
    

class PlaylistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        playlists = Playlist.objects.filter(user=request.user)
        serializer = PlaylistSerializer(playlists, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PlaylistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)


from django.core.management import call_command


class AddSongToPlaylistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PlaylistSongSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Song added to playlist"})
        return Response(serializer.errors)


class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        song_id = request.data.get('song_id')
        song_metadata = request.data.get('song_metadata') # Optional metadata for external songs
        
        if not song_id:
            return Response({"error": "song_id is required"}, status=400)
        
        song = None
        # 1. Try to find by DB ID or External ID
        song = Song.objects.filter(id=song_id if isinstance(song_id, int) and song_id < 1000000 else None).first()
        if not song:
            song = Song.objects.filter(external_id=str(song_id)).first()

        # 2. If not found and metadata provided, CREATE it
        if not song and song_metadata:
            from .models import Artist
            artist_name = song_metadata.get('artist', 'Unknown Artist')
            artist, _ = Artist.objects.get_or_create(name=artist_name)
            
            song = Song.objects.create(
                title=song_metadata.get('title', 'Untitled'),
                artist=artist,
                external_id=str(song_id),
                source=song_metadata.get('source', 'itunes'),
                preview_url=song_metadata.get('previewUrl'),
                artwork_url=song_metadata.get('artwork'),
                album=song_metadata.get('album'),
                genre=song_metadata.get('genre'),
            )

        if not song:
            return Response({"error": "Song not found and no metadata provided for sync."}, status=404)

        # 3. Toggle Like
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


class SyncLatestSongsView(APIView):
    permission_classes = [AllowAny] # Allow for demo/automation

    def post(self, request):
        try:
            call_command('sync_latest_songs')
            return Response({"message": "Latest songs synced successfully!"})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


from .utils.youtube_resolver import resolve_youtube_audio

class ResolveAudioView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        title = request.data.get('title')
        artist = request.data.get('artist')
        
        if not title or not artist:
            return Response({"error": "title and artist are required"}, status=400)
        
        query = f"{artist} - {title} official audio"
        audio_url = resolve_youtube_audio(query)
        
        if audio_url:
            return Response({"audio_url": audio_url})
        else:
            return Response({"error": "Could not resolve full audio"}, status=404)