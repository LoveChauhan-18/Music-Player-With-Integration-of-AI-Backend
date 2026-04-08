from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Song, Artist, Playlist, PlaylistSong

User = get_user_model()

# ------------------------
# Register Serializer
# ------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


# ------------------------
# Artist Serializer
# ------------------------
class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['id', 'name']


# ------------------------
# Song Serializer
# ------------------------
class SongSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(),
        source='artist',
        write_only=True
    )

    class Meta:
        model = Song
        fields = [
            'id', 'title', 'artist', 'artist_id', 'audio_file', 
            'preview_url', 'artwork_url', 'album', 'genre', 'plays', 
            'external_id', 'source', 'created_at'
        ]

# ------------------------
# Playlist Serializer
# ------------------------
class PlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = ['id', 'name']


# ------------------------
# PlaylistSong Serializer
# ------------------------
class PlaylistSongSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistSong
        fields = ['id', 'playlist', 'song']        