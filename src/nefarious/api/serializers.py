from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie,
    PERM_CAN_WATCH_IMMEDIATELY_TV, PERM_CAN_WATCH_IMMEDIATELY_MOVIE,
    WatchTVSeason,
)
from nefarious.tmdb import get_tmdb_client


class UserReferenceSerializerMixin(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )


class NefariousSettingsSerializer(serializers.ModelSerializer):
    tmdb_configuration = serializers.JSONField(required=False)
    jackett_indexers_seed = serializers.JSONField(required=False)

    class Meta:
        model = NefariousSettings
        fields = '__all__'

    def create(self, validated_data):

        # save tmdb configuration settings on creation
        nefarious_settings = NefariousSettings(**validated_data)
        tmdb_client = get_tmdb_client(nefarious_settings)
        configuration = tmdb_client.Configuration()
        validated_data['tmdb_configuration'] = configuration.info()

        return super().create(validated_data)


class NefariousPartialSettingsSerializer(serializers.ModelSerializer):
    tmdb_configuration = serializers.JSONField(required=False, read_only=True)

    class Meta:
        model = NefariousSettings
        fields = ('tmdb_configuration',)


class WatchMovieSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):

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


class WatchTVEpisodeSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    tmdb_show_id = serializers.SerializerMethodField()

    def get_name(self, obj: WatchTVEpisode):
        return str(obj)

    def get_poster_image_url(self, obj: WatchTVSeason):
        return obj.watch_tv_show.poster_image_url

    def get_tmdb_show_id(self, obj: WatchTVSeason):
        return obj.watch_tv_show.tmdb_show_id

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
