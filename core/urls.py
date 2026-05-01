from .views import (
    RegisterView, SongListCreateView, SongDetailView, 
    PlaylistView, AddSongToPlaylistView, SyncLatestSongsView,
    ToggleLikeView, UserLikedSongsView, ResolveAudioView,
    ProxyAudioView, ElevenLabsVoiceView, GenerateVocalView,
    PodcastListView, CartoonListView, AnimeListView,
    RedeployView, SelfCheckView,
)
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view()),
    path('login/', csrf_exempt(TokenObtainPairView.as_view())), 

    # Song APIs
    path('songs/', SongListCreateView.as_view()),
    path('songs/<int:pk>/', SongDetailView.as_view()),
    path('songs/sync/', SyncLatestSongsView.as_view()),

    path('playlists/', PlaylistView.as_view()),
    path('playlists/add-song/', AddSongToPlaylistView.as_view()),

    path('songs/like/', ToggleLikeView.as_view()),
    path('songs/liked/', UserLikedSongsView.as_view()),
    path('songs/resolve-audio/', ResolveAudioView.as_view()),
    path('songs/resolve-audio', ResolveAudioView.as_view()), # Alias without slash
    path('resolve-audio/', ResolveAudioView.as_view()), # Alias for compatibility
    path('resolve-audio', ResolveAudioView.as_view()), # Alias for compatibility
    path('resolve/', ResolveAudioView.as_view()), # Alias for compatibility
    path('resolve', ResolveAudioView.as_view()), # Alias for compatibility
    path('podcasts/', PodcastListView.as_view()),
    path('cartoons/', CartoonListView.as_view()),
    path('anime/', AnimeListView.as_view()),
    path('redeploy/', RedeployView.as_view()),
    path('self-check/', SelfCheckView.as_view()),
    path('proxy-audio/', ProxyAudioView.as_view()),
    path('ai/voices/', ElevenLabsVoiceView.as_view()),
    path('ai/generate-vocal/', GenerateVocalView.as_view()),
]