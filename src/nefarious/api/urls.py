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
router.register(r'users', viewsets.UserViewSet)
router.register(r'user', viewsets.CurrentUserViewSet)
router.register(r'watch-movie', viewsets.WatchMovieViewSet)

urlpatterns = [

    # viewsets
    path('', include(router.urls)),

    # views
    path('search/torrents/', views.SearchTorrentsView.as_view()),
    path('download/torrents/', views.DownloadTorrentsView.as_view()),
    path('current/torrents/', views.CurrentTorrentsView.as_view()),
    path('search/media/', views.SearchMediaView.as_view()),
    path('search/similar/media/', views.SearchSimilarMediaView.as_view()),
    path('search/recommended/media/', views.SearchRecommendedMediaView.as_view()),
    path('search/media/<str:media_type>/<int:media_id>/', views.MediaDetailView.as_view()),
    path('search/media/<str:media_type>/<int:media_id>/videos/', views.VideosView.as_view()),
    path('discover/media/<str:media_type>/', views.DiscoverMediaView.as_view()),
    path('genres/<str:media_type>/', views.GenresView.as_view()),
    path('quality-profiles/', views.QualityProfilesView.as_view()),
    path('auth/', views.ObtainAuthTokenView.as_view()),  # authenticates user and returns token
    path('git-commit/', views.GitCommitView.as_view()),  # returns this app's git commit
]
