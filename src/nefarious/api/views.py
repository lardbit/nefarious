import os
import logging
from django.conf import settings
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework import views
from nefarious.api.serializers import (
    WatchMovieSerializer, WatchTVShowSerializer, WatchTVEpisodeSerializer, WatchTVSeasonRequestSerializer, WatchTVSeasonSerializer,
    TransmissionTorrentSerializer,)
from nefarious.models import NefariousSettings, WatchMovie, WatchTVShow, WatchTVEpisode, WatchTVSeasonRequest, WatchTVSeason
from nefarious.search import MEDIA_TYPE_MOVIE, MEDIA_TYPE_TV, SearchTorrents
from nefarious.quality import PROFILES
from nefarious.transmission import get_transmission_client
from nefarious.tmdb import get_tmdb_client
from nefarious.utils import trace_torrent_url, swap_jackett_host, is_magnet_url

CACHE_MINUTE = 60
CACHE_HOUR = CACHE_MINUTE * 60
CACHE_HALF_DAY = CACHE_HOUR * 12
CACHE_DAY = CACHE_HALF_DAY * 2
CACHE_WEEK = CACHE_DAY * 7


class ObtainAuthTokenView(ObtainAuthToken):
    """
    Overridden to not require any authentication classes (ie. csrf).
    Helpful on the auth/login url
    """
    authentication_classes = ()


class GitCommitView(views.APIView):
    def get(self, request):
        path = os.path.join(settings.BASE_DIR, '.commit')
        commit = None
        if os.path.exists(path):
            with open(path) as fh:
                commit = fh.read().strip()
        return Response({
            'commit': commit,
        })


class MediaDetailView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request, media_type, media_id):
        nefarious_settings = NefariousSettings.get()
        tmdb = get_tmdb_client(nefarious_settings)

        params = {
            'language': nefarious_settings.language,
        }

        if media_type == MEDIA_TYPE_MOVIE:
            movie = tmdb.Movies(media_id)
            response = movie.info(**params)
        else:
            tv = tmdb.TV(media_id)
            response = tv.info(**params)
            # omit season "0" -- special episodes
            response['seasons'] = [season for season in response['seasons'] if season['season_number'] > 0]
            for season in response['seasons']:
                seasons_request = tmdb.TV_Seasons(response['id'], season['season_number'])
                seasons = seasons_request.info(**params)
                season['episodes'] = seasons['episodes']

        return Response(response)


class SearchMediaView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request):
        media_type = request.query_params.get('media_type', MEDIA_TYPE_TV)
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        nefarious_settings = NefariousSettings.get()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        query = request.query_params.get('q')

        params = {
            'query': query,
            'language': nefarious_settings.language,
        }

        # search for media
        search = tmdb.Search()

        if media_type == MEDIA_TYPE_MOVIE:
            results = search.movie(**params)
        else:
            results = search.tv(**params)

        return Response(results)


class SearchSimilarMediaView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request):
        media_type = request.query_params.get('media_type', MEDIA_TYPE_TV)
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        if 'tmdb_media_id' not in request.query_params:
            raise ValidationError({'tmdb_media_id': ['required parameter']})

        nefarious_settings = NefariousSettings.get()

        params = {
            'language': nefarious_settings.language,
        }

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        tmdb_media_id = request.query_params.get('tmdb_media_id')

        # search for media
        if media_type == MEDIA_TYPE_MOVIE:
            similar_results = tmdb.Movies(id=tmdb_media_id).similar_movies(**params)
        else:
            similar_results = tmdb.TV(id=tmdb_media_id).similar(**params)

        return Response(similar_results)


class SearchRecommendedMediaView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request):
        media_type = request.query_params.get('media_type', MEDIA_TYPE_TV)
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        if 'tmdb_media_id' not in request.query_params:
            raise ValidationError({'tmdb_media_id': ['required parameter']})

        nefarious_settings = NefariousSettings.get()

        params = {
            'language': nefarious_settings.language,
        }

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        tmdb_media_id = request.query_params.get('tmdb_media_id')

        # search for media
        if media_type == MEDIA_TYPE_MOVIE:
            similar_results = tmdb.Movies(id=tmdb_media_id).recommendations(**params)
        else:
            similar_results = tmdb.TV(id=tmdb_media_id).recommendations(**params)

        return Response(similar_results)


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
    permission_classes = (IsAdminUser,)

    def post(self, request):
        result = {
            'success': True,
        }
        nefarious_settings = NefariousSettings.get()

        tmdb_media = request.data.get('tmdb_media', {})
        torrent_info = request.data.get('torrent', {})
        torrent_url = torrent_info.get('MagnetUri') or torrent_info.get('Link')

        if not torrent_url:
            return Response({'success': False, 'error': 'Missing torrent link'})

        media_type = request.data.get('media_type', MEDIA_TYPE_TV)

        # validate tv
        if media_type == MEDIA_TYPE_TV:
            if 'season_number' not in request.data:
                return Response({'success': False, 'error': 'Missing season_number'})

        if not is_magnet_url(torrent_url):
            torrent_url = swap_jackett_host(torrent_url, nefarious_settings)

        try:
            torrent_url = trace_torrent_url(torrent_url)
        except Exception as e:
            return Response({'success': False, 'error': 'An unknown error occurred', 'error_detail': str(e)})

        logging.info('adding torrent: {}'.format(torrent_url))

        # add torrent
        transmission_client = get_transmission_client(nefarious_settings)
        transmission_session = transmission_client.session_stats()

        tmdb = get_tmdb_client(nefarious_settings)

        # set download paths and associate torrent with watch instance
        if media_type == MEDIA_TYPE_MOVIE:
            tmdb_request = tmdb.Movies(tmdb_media['id'])
            tmdb_movie = tmdb_request.info()
            watch_media = WatchMovie(
                user=request.user,
                tmdb_movie_id=tmdb_movie['id'],
                name=tmdb_movie['title'],
                poster_image_url=nefarious_settings.get_tmdb_poster_url(tmdb_movie['poster_path']),
                release_date=parse_date(tmdb_movie['release_date'] or ''),
            )
            watch_media.save()
            download_dir = os.path.join(
                transmission_session.download_dir, nefarious_settings.transmission_movie_download_dir.lstrip('/'))
            result['watch_movie'] = WatchMovieSerializer(watch_media).data
        else:
            tmdb_request = tmdb.TV(tmdb_media['id'])
            tmdb_show = tmdb_request.info()

            watch_tv_show, _ = WatchTVShow.objects.get_or_create(
                tmdb_show_id=tmdb_show['id'],
                defaults=dict(
                    user=request.user,
                    name=tmdb_show['name'],
                    poster_image_url=nefarious_settings.get_tmdb_poster_url(tmdb_show['poster_path']),
                )
            )

            result['watch_tv_show'] = WatchTVShowSerializer(watch_tv_show).data

            # single episode
            if 'episode_number' in request.data:
                tmdb_request = tmdb.TV_Episodes(tmdb_media['id'], request.data['season_number'], request.data['episode_number'])
                tmdb_episode = tmdb_request.info()
                watch_media = WatchTVEpisode(
                    user=request.user,
                    watch_tv_show=watch_tv_show,
                    tmdb_episode_id=tmdb_episode['id'],
                    season_number=request.data['season_number'],
                    episode_number=request.data['episode_number'],
                    release_date=parse_date(tmdb_episode['air_date'] or '')
                )
                watch_media.save()
                result['watch_tv_episode'] = WatchTVEpisodeSerializer(watch_media).data
            # entire season
            else:
                season_result = tmdb.TV_Seasons(tmdb_show['id'], request.data['season_number'])
                season_data = season_result.info()
                # create the season request
                watch_tv_season_request, _ = WatchTVSeasonRequest.objects.get_or_create(
                    watch_tv_show=watch_tv_show,
                    season_number=request.data['season_number'],
                    defaults=dict(
                        user=request.user,
                        collected=True,  # set collected since we're directly downloading a torrent
                        release_date=parse_date(season_data['air_date'] or '')
                    ),
                )
                # create the actual watch season instance
                watch_media = WatchTVSeason(
                    user=request.user,
                    watch_tv_show=watch_tv_show,
                    season_number=request.data['season_number'],
                    release_date=parse_date(season_data['air_date'] or '')
                )
                watch_media.save()

                # return the season request vs the watch instance
                result['watch_tv_season_request'] = WatchTVSeasonRequestSerializer(watch_tv_season_request).data

            download_dir = os.path.join(
                transmission_session.download_dir, nefarious_settings.transmission_tv_download_dir.lstrip('/'))

        torrent = transmission_client.add_torrent(
            torrent_url,
            paused=settings.DEBUG,
            download_dir=download_dir,
        )
        watch_media.transmission_torrent_hash = torrent.hashString
        watch_media.save()

        return Response(result)


class CurrentTorrentsView(views.APIView):

    def get(self, request):
        nefarious_settings = NefariousSettings.get()
        transmission_client = get_transmission_client(nefarious_settings)

        watch_movies = request.query_params.getlist('watch_movies', [])
        watch_tv_shows = request.query_params.getlist('watch_tv_shows', [])

        results = []
        querysets = []

        # movies
        if watch_movies:
            querysets.append(
                WatchMovie.objects.filter(id__in=watch_movies))
        # tv shows
        if watch_tv_shows:
            querysets.append(
                WatchTVEpisode.objects.filter(watch_tv_show__id__in=watch_tv_shows))
            querysets.append(
                WatchTVSeason.objects.filter(watch_tv_show__id__in=watch_tv_shows))

        for qs in querysets:

            for media in qs:

                if isinstance(media, WatchTVSeason):
                    media_serializer = WatchTVSeasonSerializer
                elif isinstance(media, WatchTVEpisode):
                    media_serializer = WatchTVEpisodeSerializer
                else:
                    media_serializer = WatchMovieSerializer

                result = {
                    'watchMedia': media_serializer(media).data,
                }

                if media.transmission_torrent_hash:

                    try:
                        torrent = transmission_client.get_torrent(media.transmission_torrent_hash)
                    except (KeyError, ValueError):  # torrent no longer exists or was invalid
                        pass
                    except Exception as e:
                        logging.error(str(e))
                        raise e
                    else:
                        result['torrent'] = TransmissionTorrentSerializer(torrent).data

                results.append(result)

        return Response(results)


class DiscoverMediaView(views.APIView):

    @method_decorator(cache_page(CACHE_WEEK))
    def get(self, request, media_type):
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        nefarious_settings = NefariousSettings.get()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        args = request.query_params.copy()
        args['language'] = nefarious_settings.language

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

        nefarious_settings = NefariousSettings.get()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)
        args = request.query_params.copy()
        args['language'] = nefarious_settings.language

        genres = tmdb.Genres()

        if media_type == MEDIA_TYPE_MOVIE:
            results = genres.movie_list(**args)
        else:
            results = genres.tv_list(**args)

        return Response(results)


class VideosView(views.APIView):

    @method_decorator(cache_page(CACHE_DAY))
    def get(self, request, media_type, media_id):
        assert media_type in [MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE]

        nefarious_settings = NefariousSettings.get()

        # prepare query
        tmdb = get_tmdb_client(nefarious_settings)

        if media_type == MEDIA_TYPE_MOVIE:
            result = tmdb.Movies(media_id)
        else:
            result = tmdb.TV(media_id)

        return Response(result.videos())


class QualityProfilesView(views.APIView):

    def get(self, request):
        return Response({'profiles': [p.name for p in PROFILES]})
