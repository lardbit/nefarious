from django.urls import path, include
from rest_framework import routers
from nefarious.api import viewsets
from nefarious.api import views

router = routers.DefaultRouter()
router.register(r'settings', viewsets.SettingsViewSet)
router.register(r'watch-tv-show', viewsets.WatchTVShowViewSet)
router.register(r'watch-tv-season', viewsets.WatchTVSeasonViewSet)
router.register(r'watch-tv-season-request', viewsets.WatchTVSeasonRequestViewSet)
router.register(r'watch-tv-episode', viewsets.WatchTVEpisodeViewSet)
router.register(r'users', viewsets.UserViewSet, base_name='users')  # specify base_name since it shares a queryset
router.register(r'user', viewsets.CurrentUserViewSet)
router.register(r'watch-movie', viewsets.WatchMovieViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search/torrents/', viewsets.SearchTorrentsView.as_view()),
    path('download/torrents/', viewsets.DownloadTorrentsView.as_view()),
    path('current/torrents/', viewsets.CurrentTorrentsView.as_view()),
    path('search/media/', viewsets.SearchMediaView.as_view()),
    path('search/similar/media/', viewsets.SearchSimilarMediaView.as_view()),
    path('search/recommended/media/', viewsets.SearchRecommendedMediaView.as_view()),
    path('search/media/<str:media_type>/<int:media_id>/', viewsets.MediaDetailView.as_view()),
    path('search/media/<str:media_type>/<int:media_id>/videos/', viewsets.VideosView.as_view()),
    path('discover/media/<str:media_type>/', viewsets.DiscoverMediaView.as_view()),
    path('genres/<str:media_type>/', viewsets.GenresView.as_view()),
    path('quality-profiles/', viewsets.QualityProfilesView.as_view()),
    path('auth/', views.ObtainAuthToken.as_view()),  # authenticates user and returns token
]
