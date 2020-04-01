from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie,
    PERM_CAN_WATCH_IMMEDIATELY_TV, PERM_CAN_WATCH_IMMEDIATELY_MOVIE,
    WatchTVSeason, WatchTVSeasonRequest,
)


class UserReferenceSerializerMixin(serializers.ModelSerializer):
    # this automatically includes the current user in the serializer so the request doesn't have to send it along
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )


class NefariousSettingsSerializer(serializers.ModelSerializer):
    tmdb_configuration = serializers.JSONField(required=False)
    keyword_search_filters = serializers.JSONField(required=False)
    tmdb_languages = serializers.JSONField(required=False)
    jackett_default_token = serializers.ReadOnlyField(default=NefariousSettings.JACKETT_TOKEN_DEFAULT)
    websocket_url = serializers.SerializerMethodField()
    is_debug = serializers.SerializerMethodField()

    def get_websocket_url(self, obj):
        return settings.WEBSOCKET_URL

    def get_is_debug(self, obj):
        return settings.DEBUG

    class Meta:
        model = NefariousSettings
        fields = '__all__'


class NefariousPartialSettingsSerializer(NefariousSettingsSerializer):
    # redefine as read-only
    tmdb_configuration = serializers.JSONField(required=False, read_only=True)

    class Meta:
        model = NefariousSettings
        # only include specific fields
        fields = ('tmdb_configuration', 'jackett_default_token', 'websocket_url', 'is_debug')


class WatchMovieSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    # necessary for outputting the user since UserReferenceSerializerMixin automatically includes "user" as an input/hidden field for convenience
    requested_by = serializers.SerializerMethodField()

    def get_requested_by(self, watch_movie: WatchMovie):
        return watch_movie.user.username

    class Meta:
        model = WatchMovie
        fields = '__all__'


class WatchTVShowSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = WatchTVShow
        fields = '__all__'


class WatchTVSeasonSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    tmdb_show_id = serializers.SerializerMethodField()

    def get_name(self, obj: WatchTVSeason):
        return str(obj)

    def get_poster_image_url(self, obj: WatchTVSeason):
        return obj.watch_tv_show.poster_image_url

    def get_tmdb_show_id(self, obj: WatchTVSeason):
        return obj.watch_tv_show.tmdb_show_id

    class Meta:
        model = WatchTVSeason
        fields = '__all__'


class WatchTVSeasonRequestSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    # necessary for outputting the user since UserReferenceSerializerMixin automatically includes "user" as an input/hidden field for convenience
    requested_by = serializers.SerializerMethodField()

    def get_requested_by(self, watch_tv_season_request: WatchTVSeasonRequest):
        return watch_tv_season_request.user.username

    def get_name(self, obj: WatchTVSeasonRequest):
        return str(obj)

    class Meta:
        model = WatchTVSeasonRequest
        fields = '__all__'


class WatchTVEpisodeSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    tmdb_show_id = serializers.SerializerMethodField()
    requested_by = serializers.SerializerMethodField()

    def get_name(self, obj: WatchTVEpisode):
        return str(obj)

    def get_poster_image_url(self, obj: WatchTVEpisode):
        return obj.watch_tv_show.poster_image_url

    def get_tmdb_show_id(self, obj: WatchTVEpisode):
        return obj.watch_tv_show.tmdb_show_id

    def get_requested_by(self, obj: WatchTVEpisode):
        return obj.user.username

    class Meta:
        model = WatchTVEpisode
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    can_immediately_watch_tv_shows = serializers.SerializerMethodField()
    can_immediately_watch_movies = serializers.SerializerMethodField()

    def get_can_immediately_watch_movies(self, user: User):
        return user.is_staff or user.has_perm('app.{}'.format(PERM_CAN_WATCH_IMMEDIATELY_MOVIE))

    def get_can_immediately_watch_tv_shows(self, user: User):
        return user.is_staff or user.has_perm('app.{}'.format(PERM_CAN_WATCH_IMMEDIATELY_TV))

    def update(self, instance, validated_data):
        # update password if a new one was supplied
        user = super().update(instance, validated_data)  # type: User
        if 'password' in self.initial_data:
            user.set_password(self.initial_data['password'])
            user.save()
        return user

    def create(self, validated_data):
        # a password must exist when creating a new user
        if 'password' not in self.initial_data:
            raise ValidationError({'password': ['Please supply a new password for this user']})
        user = super().create(validated_data)  # type: User
        user.set_password(self.initial_data['password'])
        user.save()
        return user

    class Meta:
        model = User
        fields = (
            'id', 'username', 'is_staff',
            'can_immediately_watch_tv_shows', 'can_immediately_watch_movies',
        )


class TransmissionTorrentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    hashString = serializers.CharField()
    name = serializers.CharField()
    date_active = serializers.DateTimeField()
    date_added = serializers.DateTimeField()
    date_done = serializers.DateTimeField()
    date_started = serializers.DateTimeField()
    format_eta = serializers.SerializerMethodField()
    progress = serializers.IntegerField()
    status = serializers.CharField()
    files = serializers.SerializerMethodField()

    def get_files(self, torrent):
        return torrent.files()

    def get_format_eta(self, torrent):
        return torrent.format_eta()
