import logging
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from nefarious.api.mixins import UserReferenceViewSetMixin, BlacklistAndRetryMixin
from nefarious.quality import PROFILES
from nefarious.transmission import get_transmission_client
from nefarious.tmdb import get_tmdb_client
from nefarious.api.serializers import (
    NefariousSettingsSerializer, WatchTVEpisodeSerializer, WatchTVShowSerializer,
    UserSerializer, WatchMovieSerializer, NefariousPartialSettingsSerializer,
    TransmissionTorrentSerializer, WatchTVSeasonSerializer)
from nefarious.models import NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, WatchTVSeason
from nefarious.search import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, SearchTorrents
from nefarious.tasks import watch_tv_episode_task, watch_tv_show_season_task, watch_movie_task
from nefarious.utils import (
    trace_torrent_url, swap_jackett_host, is_magnet_url,
    verify_settings_jackett, verify_settings_transmission, verify_settings_tmdb,
)

CACHE_MINUTE = 60
CACHE_HOUR = CACHE_MINUTE * 60
CACHE_HALF_DAY = CACHE_HOUR * 12
CACHE_DAY = CACHE_HALF_DAY * 2
CACHE_WEEK = CACHE_DAY * 7


class WatchMovieViewSet(BlacklistAndRetryMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchMovie.objects.all()
    serializer_class = WatchMovieSerializer

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


class WatchTVShowViewSet(UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchTVShow.objects.all()
    serializer_class = WatchTVShowSerializer

    @action(methods=['post'], detail=True, url_path='entire-season')
    def watch_entire_season(self, request, pk):
        watch_tv_show = self.get_object()  # type: WatchTVShow
        data = request.query_params or request.data

        if 'season_number' not in data:
            raise ValidationError({'season_number': ['This field is required']})

        watch_tv_season, was_created = WatchTVSeason.objects.get_or_create(
            user=request.user,
            watch_tv_show=watch_tv_show,
            season_number=data['season_number'],
        )

        if was_created:
            watch_tv_season.save()

        # create a task to download the whole season
        watch_tv_show_season_task.delay(watch_tv_season.id)

        return Response(
            WatchTVSeasonSerializer(watch_tv_season).data)


class WatchTVSeasonViewSet(BlacklistAndRetryMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchTVSeason.objects.all()
    serializer_class = WatchTVSeasonSerializer

    def _watch_media_task(self, watch_media_id: int):
        watch_tv_show_season_task.delay(watch_media_id)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        # create a task to download the episode
        watch_tv_show_season_task.delay(serializer.instance.id)


class WatchTVEpisodeViewSet(BlacklistAndRetryMixin, UserReferenceViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchTVEpisode.objects.all()
    serializer_class = WatchTVEpisodeSerializer

    def _watch_media_task(self, watch_media_id: int):
        watch_tv_episode_task.delay(watch_media_id)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        # create a task to download the episode
        watch_tv_episode_task.delay(serializer.instance.id)


class SettingsViewSet(viewsets.ModelViewSet):
    queryset = NefariousSettings.objects.all()

    @action(methods=['get'], detail=True)
    def verify(self, request, pk):
        nefarious_settings = self.queryset.get(id=pk)
        try:
            verify_settings_jackett(nefarious_settings)
            verify_settings_tmdb(nefarious_settings)
            verify_settings_transmission(nefarious_settings)
        except Exception as e:
            raise ValidationError(str(e))
        return Response()

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return NefariousSettingsSerializer
        return NefariousPartialSettingsSerializer


class CurrentUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return self.queryset.filter(username=self.request.user.username)


class MediaDetailView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request, media_type, media_id):
        nefarious_settings = NefariousSettings.singleton()
        tmdb = get_tmdb_client(nefarious_settings)

        if media_type == MEDIA_TYPE_MOVIE:
            movie = tmdb.Movies(media_id)
            response = movie.info()
        else:
            tv = tmdb.TV(media_id)
            response = tv.info()
            for season in response['seasons']:
                seasons_request = tmdb.TV_Seasons(response['id'], season['season_number'])
                seasons = seasons_request.info()
                season['episodes'] = seasons['episodes']

        return Response(response)


class SearchMediaView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request):
        media_type = request.query_params.get('media_type', MEDIA_TYPE_TV)
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        nefarious_settings = NefariousSettings.singleton()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        query = request.query_params.get('q')

        # search for media
        search = tmdb.Search()

        if media_type == MEDIA_TYPE_MOVIE:
            results = search.movie(query=query)
        else:
            results = search.tv(query=query)

        return Response(results)


class SearchTorrentsView(views.APIView):

    @method_decorator(cache_page(CACHE_HALF_DAY))
    def get(self, request):
        query = request.query_params.get('q')
        media_type = request.query_params.get('media_type', MEDIA_TYPE_MOVIE)
        search = SearchTorrents(media_type, query)
        if not search.ok:
            return Response({'error': search.error_content}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(search.results)


class DownloadTorrentsView(views.APIView):

    def post(self, request):
        nefarious_settings = NefariousSettings.singleton()
        torrent = request.data.get('torrent')
        if not is_magnet_url(torrent):
            torrent = swap_jackett_host(torrent, nefarious_settings)

        if not torrent:
            return Response({'success': False, 'error': 'Missing torrent link'})

        try:
            torrent = trace_torrent_url(torrent)
        except Exception as e:
            return Response({'success': False, 'error': 'An unknown error occurred', 'error_detail': str(e)})

        logging.info('adding torrent: {}'.format(torrent))

        # add torrent
        transmission_client = get_transmission_client(nefarious_settings)
        transmission_client.add_torrent(torrent, paused=True)
        
        return Response({'success': True})


class CurrentTorrentsView(views.APIView):

    def get(self, request):
        nefarious_settings = NefariousSettings.singleton()
        transmission_client = get_transmission_client(nefarious_settings)
        tmdb_movie_ids = request.query_params.getlist('tmdb_movie_ids')
        tmdb_episode_ids = request.query_params.getlist('tmdb_episode_ids')
        tmdb_season_numbers = request.query_params.getlist('tmdb_season_numbers')
        tmdb_show_id = request.query_params.get('tmdb_show_id')

        querysets = []
        torrent_hashes = []

        # movies
        if tmdb_movie_ids:
            querysets.append(
                WatchMovie.objects.filter(tmdb_movie_id__in=tmdb_movie_ids))
        # tv episodes
        if tmdb_episode_ids:
            querysets.append(
                WatchTVEpisode.objects.filter(tmdb_episode_id__in=tmdb_episode_ids))
        # tv seasons
        if tmdb_show_id and tmdb_season_numbers:
            querysets.append(
                WatchTVSeason.objects.filter(tmdb_show_id=tmdb_show_id, season_number__in=tmdb_season_numbers))

        for query in querysets:
            torrent_hashes += [media.transmission_torrent_hash for media in query if media.transmission_torrent_hash]

        try:
            result = transmission_client.get_torrents(torrent_hashes)
        except Exception as e:
            logging.error(str(e))
            raise ValidationError(str(e))

        return Response(TransmissionTorrentSerializer(result, many=True).data)


class DiscoverMediaView(views.APIView):

    @method_decorator(cache_page(CACHE_WEEK))
    def get(self, request, media_type):
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        nefarious_settings = NefariousSettings.singleton()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        args = request.query_params
        discover = tmdb.Discover()

        if media_type == MEDIA_TYPE_MOVIE:
            results = discover.movie(**args)
        else:
            results = discover.tv(**args)

        return Response(results)


class GenresView(views.APIView):

    @method_decorator(cache_page(CACHE_WEEK))
    def get(self, request, media_type):
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        nefarious_settings = NefariousSettings.singleton()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        args = request.query_params
        genres = tmdb.Genres()

        if media_type == MEDIA_TYPE_MOVIE:
            results = genres.movie_list(**args)
        else:
            results = genres.tv_list(**args)

        return Response(results)


class QualityProfilesView(views.APIView):

    def get(self, request):
        return Response({'profiles': [p.name for p in PROFILES]})
