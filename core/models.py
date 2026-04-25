from django.db import models
from django.conf import settings

class Artist(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(
        Artist,
        on_delete=models.CASCADE,
        related_name='songs'
    )
    audio_file = models.FileField(upload_to='songs/', null=True, blank=True)
    preview_url = models.URLField(max_length=500, null=True, blank=True)
    artwork_url = models.URLField(max_length=500, null=True, blank=True)
    album = models.CharField(max_length=255, null=True, blank=True)
    genre = models.CharField(max_length=100, null=True, blank=True)
    plays = models.IntegerField(default=0)
    external_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    source = models.CharField(max_length=50, default='local')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.artist.name}"


class Playlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='playlists'
    )
    name = models.CharField(max_length=255)
    songs = models.ManyToManyField(Song, through='PlaylistSong', related_name='playlists')

    def __str__(self):
        return self.name


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(
        Playlist,
        on_delete=models.CASCADE,
        related_name='playlist_songs'
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='song_playlists'
    )

    def __str__(self):
        return f"{self.playlist.name} - {self.song.title}"