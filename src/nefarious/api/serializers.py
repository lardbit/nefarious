import logging
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie,
    PERM_CAN_WATCH_IMMEDIATELY_TV, PERM_CAN_WATCH_IMMEDIATELY_MOVIE,
)
from nefarious.tmdb import get_tmdb_client
from nefarious.utils import verify_settings_jackett, verify_settings_transmission, verify_settings_tmdb


class UserReferenceSerializerMixin(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )


class NefariousSettingsSerializer(serializers.ModelSerializer):
    tmdb_configuration = serializers.JSONField(required=False)

    class Meta:
        model = NefariousSettings
        fields = '__all__'

    def update(self, instance, validated_data):
        test_settings = NefariousSettings(**validated_data)

        # verify settings
        try:
            verify_settings_jackett(test_settings)
            verify_settings_tmdb(test_settings)
            verify_settings_transmission(test_settings)
        except Exception as e:
            raise ValidationError(str(e))
        return super().update(instance, validated_data)

    def create(self, validated_data):
        test_settings = NefariousSettings(**validated_data)

        # verify/fetch tmdb configuration settings and include in serializer data
        try:
            tmdb_client = get_tmdb_client(test_settings)
            configuration = tmdb_client.Configuration()
            validated_data['tmdb_configuration'] = configuration.info()
        except Exception as e:
            logging.error(str(e))
            raise ValidationError('Could not fetch TMDB configuration')

        # verify settings
        try:
            verify_settings_jackett(test_settings)
            verify_settings_transmission(test_settings)
        except Exception as e:
            raise ValidationError(str(e))

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


class WatchTVEpisodeSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return '{}x{}'.format(obj.season_number, obj.episode_number)

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

    class Meta:
        model = User
        fields = (
            'username', 'is_staff', 'email',
            'can_immediately_watch_tv_shows', 'can_immediately_watch_movies',
        )


class TransmissionTorrentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
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
