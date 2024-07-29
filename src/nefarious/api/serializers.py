from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie,
    PERM_CAN_WATCH_IMMEDIATELY_TV, PERM_CAN_WATCH_IMMEDIATELY_MOVIE,
    WatchTVSeason, WatchTVSeasonRequest, TorrentBlacklist, QualityProfile,
)


class UserReferenceSerializerMixin(serializers.ModelSerializer):
    # this automatically includes the current user in the serializer so the request doesn't have to send it along
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    # necessary for outputting the user since this mixin automatically includes "user" as an input/hidden field
    requested_by = serializers.SerializerMethodField()

    def get_requested_by(self, watch_media):
        return watch_media.user.username


class NefariousSettingsSerializer(serializers.ModelSerializer):
    tmdb_configuration = serializers.JSONField(required=False)
    keyword_search_filters = serializers.JSONField(required=False)
    tmdb_languages = serializers.JSONField(required=False)
    jackett_default_token = serializers.ReadOnlyField(default=NefariousSettings.JACKETT_TOKEN_DEFAULT)
    websocket_url = serializers.SerializerMethodField()
    is_debug = serializers.SerializerMethodField()
    host_download_path = serializers.SerializerMethodField()
    # TODO - need to handle saving
    quality_profile_tv = serializers.SerializerMethodField()
    quality_profile_movies = serializers.SerializerMethodField()

    def get_websocket_url(self, obj):
        return settings.WEBSOCKET_URL

    def get_is_debug(self, obj):
        return settings.DEBUG

    def get_host_download_path(self, obj):
        return settings.HOST_DOWNLOAD_PATH

    def get_quality_profile_tv(self, obj):
        return QualityProfileSerializer(obj.quality_profile_tv).data

    def get_quality_profile_movies(self, obj):
        return QualityProfileSerializer(obj.quality_profile_movies).data

    class Meta:
        model = NefariousSettings
        fields = '__all__'


class NefariousPartialSettingsSerializer(NefariousSettingsSerializer):
    # redefine as read-only
    tmdb_configuration = serializers.JSONField(required=False, read_only=True)

    class Meta:
        model = NefariousSettings
        # only include specific fields
        fields = (
            'tmdb_configuration', 'jackett_default_token', 'websocket_url',
            'is_debug', 'preferred_media_category',
        )


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


class WatchTVSeasonRequestSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj: WatchTVSeasonRequest):
        return str(obj)

    class Meta:
        model = WatchTVSeasonRequest
        fields = '__all__'


class WatchTVEpisodeSerializer(UserReferenceSerializerMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    tmdb_show_id = serializers.SerializerMethodField()

    def get_name(self, obj: WatchTVEpisode):
        return str(obj)

    def get_poster_image_url(self, obj: WatchTVEpisode):
        return obj.watch_tv_show.poster_image_url

    def get_tmdb_show_id(self, obj: WatchTVEpisode):
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


class RottenTomatoesSearchResultsSerializer(serializers.Serializer):
    """
    Example structure:
    {
      "audienceScore": {
        "score": "100",
        "sentiment": "positive"
      },
      "criticsScore": {
        "certifiedAttribute": "criticscertified",
        "score": "95",
        "sentiment": "positive"
      },
      "fallbackPosterUrl": "//images.fandango.com/cms/assets/5d84d010-59b1-11ea-b175-791e911be53d--rt-poster-defaultgif.gif",
      "id": "b0abd773-8d61-4eb9-aa9d-88e0f2bbbd7c",
      "isVideo": true,
      "emsId": "b0abd773-8d61-4eb9-aa9d-88e0f2bbbd7c",
      "mediaUrl": "/m/raise_hell_the_life_and_times_of_molly_ivins",
      "mpxId": "1586014787912",
      "publicId": "KKvRGVDXcmOW",
      "posterUri": "https://resizing.flixster.com/5N_zGtISCTTAsLmd10j4oFIwkps=/180x258/v2/https://flxt.tmsimg.com/assets/p16629839_p_v8_aa.jpg",
      "releaseDateText": "Streaming Aug 30, 2019",
      "title": "Raise Hell: The Life & Times of Molly Ivins",
      "trailerUrl": "https://player.theplatform.com/p/NGweTC/pdk6_y__7B0iQTi4P/embed/select/media/KKvRGVDXcmOW",
      "type": "Movie"
    }
    """
    title = serializers.CharField()
    critics_score = serializers.CharField(source='criticsScore.score', required=False)
    audience_score = serializers.CharField(source='audienceScore.score', required=False)
    poster_path = serializers.CharField(source='posterUri')
    provider = serializers.CharField(default='rotten-tomatoes')  # added flag to know where results came from


class TorrentBlacklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorrentBlacklist
        fields = '__all__'


class QualityProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityProfile
        fields = '__all__'
