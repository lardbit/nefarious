from django_filters import rest_framework as filters
from nefarious.models import WatchMovie, WatchTVEpisode, WatchTVSeasonRequest, WatchTVSeason


class WatchMovieDateUpdatedFilter(filters.FilterSet):

    class Meta:
        model = WatchMovie
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }


class WatchTVSeasonDateUpdatedFilter(filters.FilterSet):

    class Meta:
        model = WatchTVSeason
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }


class WatchTVEpisodeDateUpdatedFilter(filters.FilterSet):

    class Meta:
        model = WatchTVEpisode
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }


class WatchTVSeasonRequestDateUpdatedFilter(filters.FilterSet):

    class Meta:
        model = WatchTVSeasonRequest
        fields = {
            'collected': ['exact'],
            'date_updated': ['gte'],
        }
