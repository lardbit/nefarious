from datetime import datetime

from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser

from nefarious import websocket
from nefarious.api.mixins import UserReferenceViewSetMixin, BlacklistAndRetryMixin, DestroyTransmissionResultMixin, WebSocketMediaMessageUpdatedMixin
from nefarious.api.permissions import IsAuthenticatedDjangoObjectUser
from nefarious.api.serializers import (
    NefariousSettingsSerializer, WatchTVEpisodeSerializer, WatchTVShowSerializer,
    UserSerializer, WatchMovieSerializer, NefariousPartialSettingsSerializer,
    WatchTVSeasonSerializer, WatchTVSeasonRequestSerializer,
)
from nefarious.models import NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, WatchTVSeason, WatchTVSeasonRequest
from nefarious.tasks import watch_tv_episode_task, watch_tv_show_season_task, watch_movie_task, send_websocket_message_task
from nefarious.utils import (
    verify_settings_jackett, verify_settings_transmission, verify_settings_tmdb,
    fetch_jackett_indexers, destroy_transmission_result)


class WatchMovieViewSet(WebSocketMediaMessageUpdatedMixin, DestroyTransmissionResultMixin, BlacklistAndRetryMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchMovie.objects.all()
    serializer_class = WatchMovieSerializer
    filter_fields = ('collected',)
    permission_classes = (IsAuthenticatedDjangoObjectUser,)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        # create a task to download the movie
        watch_movie_task.delay(serializer.instance.id)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        # create a task to download the movie
        watch_movie_task.delay(serializer.instance.id)

    def _watch_media_task(self, watch_media_id: int):
        watch_movie_task.delay(watch_media_id)


class WatchTVShowViewSet(WebSocketMediaMessageUpdatedMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchTVShow.objects.all()
    serializer_class = WatchTVShowSerializer
    permission_classes = (IsAuthenticatedDjangoObjectUser,)

    def perform_update(self, serializer):
        instance = self.get_object()  # type: WatchTVShow
        # set the auto watch date to now if it was toggled on
        if not instance.auto_watch and serializer.validated_data.get('auto_watch'):
            serializer.validated_data['auto_watch_date_updated'] = datetime.utcnow().date()
        super().perform_update(serializer)

    def perform_destroy(self, watch_tv_show: WatchTVShow):
        # delete all seasons, season requests, episodes and remove from transmission

        # delete season requests
        WatchTVSeasonRequest.objects.filter(watch_tv_show=watch_tv_show).delete()

        # delete instance and from transmission and send websocket messages
        queries = [WatchTVSeason.objects.filter(watch_tv_show=watch_tv_show), WatchTVEpisode.objects.filter(watch_tv_show=watch_tv_show)]
        for qs in queries:
            for media in qs:
                # send a websocket message that this media was removed
                media_type, data = websocket.get_media_type_and_serialized_watch_media(media)
                send_websocket_message_task.delay(websocket.ACTION_REMOVED, media_type, data)
                # delete from transmission
                destroy_transmission_result(media)
                # delete the media
                media.delete()

        return super().perform_destroy(watch_tv_show)


class WatchTVSeasonViewSet(WebSocketMediaMessageUpdatedMixin, DestroyTransmissionResultMixin, BlacklistAndRetryMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchTVSeason.objects.all()
    serializer_class = WatchTVSeasonSerializer
    permission_classes = (IsAuthenticatedDjangoObjectUser,)
    filter_fields = ('collected',)

    def _watch_media_task(self, watch_media_id: int):
        """
        blacklist & retry function to queue the new task
        """
        watch_tv_show_season_task.delay(watch_media_id)


class WatchTVSeasonRequestViewSet(WebSocketMediaMessageUpdatedMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    """
    Special viewset to monitor the request of a season, not collection of the season/media itself
    """
    queryset = WatchTVSeasonRequest.objects.all()
    serializer_class = WatchTVSeasonRequestSerializer
    permission_classes = (IsAuthenticatedDjangoObjectUser,)
    filter_fields = ('collected',)

    def perform_create(self, serializer):
        super().perform_create(serializer)

        # save a watch tv season instance to try and download the whole season immediately
        watch_tv_season, _ = WatchTVSeason.objects.get_or_create(
            watch_tv_show=WatchTVShow.objects.get(id=serializer.data['watch_tv_show']),
            season_number=serializer.data['season_number'],
            defaults=dict(
                # add non-unique constraint fields for the default values
                user=self.request.user,
                release_date=serializer.data['release_date'],
            ),
        )
        # send a websocket message for this new season
        media_type, data = websocket.get_media_type_and_serialized_watch_media(watch_tv_season)
        send_websocket_message_task.delay(websocket.ACTION_UPDATED, media_type, data)

        # delete any individual episodes (including in transmission) now that we're watching the entire season
        for episode in WatchTVEpisode.objects.filter(watch_tv_show=watch_tv_season.watch_tv_show, season_number=watch_tv_season.season_number):
            # send a websocket message for this removed episode
            media_type, data = websocket.get_media_type_and_serialized_watch_media(episode)
            send_websocket_message_task.delay(websocket.ACTION_REMOVED, media_type, data)
            # delete from transmission
            destroy_transmission_result(episode)
            # delete the episode
            episode.delete()

        # create a task to download the whole season (fallback to individual episodes if it fails)
        watch_tv_show_season_task.delay(watch_tv_season.id)

    def perform_destroy(self, watch_tv_season_request: WatchTVSeasonRequest):
        # destroy watch tv season instances as well, including any related torrents in transmission
        query_args = dict(
            watch_tv_show=watch_tv_season_request.watch_tv_show,
            season_number=watch_tv_season_request.season_number,
        )
        for season in WatchTVSeason.objects.filter(**query_args):
            # send a websocket message that this season was removed
            media_type, data = websocket.get_media_type_and_serialized_watch_media(season)
            send_websocket_message_task.delay(websocket.ACTION_REMOVED, media_type, data)
            # delete from transmission
            destroy_transmission_result(season)
            # delete the season
            season.delete()
        return super().perform_destroy(watch_tv_season_request)


class WatchTVEpisodeViewSet(WebSocketMediaMessageUpdatedMixin, DestroyTransmissionResultMixin, BlacklistAndRetryMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchTVEpisode.objects.all()
    serializer_class = WatchTVEpisodeSerializer
    permission_classes = (IsAuthenticatedDjangoObjectUser,)
    filter_fields = ('collected',)

    def _watch_media_task(self, watch_media_id: int):
        watch_tv_episode_task.delay(watch_media_id)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        # create a task to download the episode
        watch_tv_episode_task.delay(serializer.instance.id)


class SettingsViewSet(viewsets.ModelViewSet):
    queryset = NefariousSettings.objects.all()

    @action(methods=['get'], detail=True, permission_classes=(IsAdminUser,))
    def verify(self, request, pk):
        nefarious_settings = self.queryset.get(id=pk)
        try:
            verify_settings_jackett(nefarious_settings)
            verify_settings_tmdb(nefarious_settings)
            verify_settings_transmission(nefarious_settings)
        except Exception as e:
            raise ValidationError(str(e))
        return Response()

    @action(methods=['get'], detail=True, url_path='verify-jackett-indexers', permission_classes=(IsAdminUser,))
    def verify_jackett_indexers(self, request, pk):
        nefarious_settings = self.queryset.get(id=pk)
        try:
            results = verify_settings_jackett(nefarious_settings)
        except Exception as e:
            raise ValidationError(str(e))
        return Response(results.get('Indexers'))

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return NefariousSettingsSerializer
        return NefariousPartialSettingsSerializer

    @action(methods=['get'], detail=False, url_path='configured-indexers', permission_classes=(IsAdminUser,))
    def configured_indexers(self, request):
        nefarious_settings = NefariousSettings.get()
        return Response(fetch_jackett_indexers(nefarious_settings))


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return self.queryset.filter(username=self.request.user.username)
