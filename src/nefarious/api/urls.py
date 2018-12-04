from django.urls import path, include
from rest_framework import routers
from nefarious.api import viewsets
from rest_framework.authtoken import views

router = routers.DefaultRouter()
router.register(r'settings', viewsets.SettingsViewSet)
router.register(r'watch-tv-show', viewsets.WatchTVShowViewSet)
router.register(r'watch-tv-episode', viewsets.WatchTVEpisodeViewSet)
router.register(r'user', viewsets.CurrentUserViewSet)
router.register(r'watch-movie', viewsets.WatchMovieViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search/torrents/', viewsets.SearchTorrentsView.as_view()),
    path('download/torrents/', viewsets.DownloadTorrentsView.as_view()),
    path('current/torrents/<int:torrent_id>/', viewsets.CurrentTorrentsView.as_view()),
    path('current/torrents/', viewsets.CurrentTorrentsView.as_view()),
    path('search/media/', viewsets.SearchMediaView.as_view()),
    path('search/media/<str:media_type>/<int:media_id>/', viewsets.MediaDetailView.as_view()),
    path('discover/media/<str:media_type>/', viewsets.DiscoverMediaView.as_view()),
    path('auth/', views.obtain_auth_token),  # authenticates user and returns token
]