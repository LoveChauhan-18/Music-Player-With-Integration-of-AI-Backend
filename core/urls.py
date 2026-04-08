from .views import (
    RegisterView, SongListCreateView, SongDetailView, 
    PlaylistView, AddSongToPlaylistView, SyncLatestSongsView,
    ToggleLikeView, UserLikedSongsView, ResolveAudioView
)
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()), 

    # Song APIs
    path('songs/', SongListCreateView.as_view()),
    path('songs/<int:pk>/', SongDetailView.as_view()),
    path('songs/sync/', SyncLatestSongsView.as_view()),

    path('playlists/', PlaylistView.as_view()),
    path('playlists/add-song/', AddSongToPlaylistView.as_view()),

    path('songs/like/', ToggleLikeView.as_view()),
    path('songs/liked/', UserLikedSongsView.as_view()),
    path('songs/resolve-audio/', ResolveAudioView.as_view()),
]