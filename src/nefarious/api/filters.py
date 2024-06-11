from django_filters import rest_framework as filters
from nefarious.models import WatchMovie, WatchTVEpisode, WatchTVSeasonRequest, WatchTVSeason


class WatchMovieFilterSet(filters.FilterSet):

    class Meta:
        model = WatchMovie
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }


class WatchTVSeasonFilterSet(filters.FilterSet):

    class Meta:
        model = WatchTVSeason
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }


class WatchTVEpisodeFilterSet(filters.FilterSet):

    class Meta:
        model = WatchTVEpisode
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }


class WatchTVSeasonRequestFilterSet(filters.FilterSet):

    class Meta:
        model = WatchTVSeasonRequest
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }
