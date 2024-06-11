import os
from django.contrib.auth.models import User
from django.conf import settings
from jsonfield import JSONField
from django.db import models
from nefarious import media_category
from nefarious import quality

PERM_CAN_WATCH_IMMEDIATELY_TV = 'can_immediately_watch_tv'
PERM_CAN_WATCH_IMMEDIATELY_MOVIE = 'can_immediately_watch_movie'

MEDIA_TYPE_MOVIE = 'MOVIE'
MEDIA_TYPE_TV_SHOW = 'TV_SHOW'
MEDIA_TYPE_TV_SEASON = 'TV_SEASON'
MEDIA_TYPE_TV_SEASON_REQUEST = 'TV_SEASON_REQUEST'
MEDIA_TYPE_TV_EPISODE = 'TV_EPISODE'


class NefariousSettings(models.Model):
    JACKETT_TOKEN_DEFAULT = 'COPY_YOUR_JACKETT_TOKEN_HERE'

    # chosen language
    language = models.CharField(max_length=2, default='en')

    # jackett
    jackett_host = models.CharField(max_length=500, default='jackett')
    jackett_port = models.IntegerField(default=9117)
    jackett_token = models.CharField(max_length=500, default=JACKETT_TOKEN_DEFAULT)

    # transmission
    transmission_host = models.CharField(max_length=500, default='transmission')
    transmission_port = models.IntegerField(default=9091)
    transmission_user = models.CharField(max_length=500, blank=True, default='')  # credentials aren't required for transmission
    transmission_pass = models.CharField(max_length=500, blank=True, default='')  # credentials aren't required for transmission
    transmission_tv_download_dir = models.CharField(max_length=500, default='tv/', help_text='Relative to download path')
    transmission_movie_download_dir = models.CharField(max_length=500, default='movies/', help_text='Relative to download path')

    # tmbd - the movie database
    tmdb_token = models.CharField(max_length=500, default=settings.TMDB_API_TOKEN)
    tmdb_configuration = JSONField(blank=True, null=True)
    tmdb_languages = JSONField(blank=True, null=True)  # type: list

    # open subtitles
    open_subtitles_api_key = models.CharField(max_length=500, default=settings.OPENSUBTITLES_API_KEY, help_text='OpenSubtitles API Key')  # static value
    open_subtitles_username = models.CharField(max_length=500, blank=True, null=True, help_text='OpenSubtitles username')
    open_subtitles_password = models.CharField(max_length=500, blank=True, null=True, help_text='OpenSubtitles password')
    open_subtitles_user_token = models.CharField(max_length=500, blank=True, null=True, help_text='OpenSubtitles user auth token')  # generated in auth flow
    open_subtitles_auto = models.BooleanField(default=False, help_text='Whether to automatically download subtitles')

    quality_profile_tv = models.CharField(max_length=500, default=quality.PROFILE_ANY.name, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))
    quality_profile_movies = models.CharField(max_length=500, default=quality.PROFILE_HD_720P_1080P.name, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))

    # whether to allow hardcoded subtitles
    allow_hardcoded_subs = models.BooleanField(default=False)

    # whether to enable video detection features (e.g. fake/spam)
    enable_video_detection = models.BooleanField(default=False)

    # expects keyword/boolean pairs like {"x265": false, "265": false}
    keyword_search_filters = JSONField(blank=True, null=True)  # type: dict

    # apprise notifications - https://github.com/caronc/apprise/tree/v0.9.3
    apprise_notification_url = models.CharField(max_length=1000, blank=True)

    # category of media the user prefers: movie or tv...
    preferred_media_category = models.CharField(
        max_length=10,
        default=media_category.MEDIA_MOVIE_CATEGORY,
        choices=media_category.MEDIA_CATEGORIES,
    )

    # handling of "stuck" downloads and how many days to blacklist a torrent if it's been stuck
    stuck_download_handling_enabled = models.BooleanField(default=False, help_text='Whether to enable stuck download handling by blacklisting stuck torrents')
    stuck_download_handling_days = models.IntegerField(default=3, help_text='How many days to wait before blacklisting stuck downloads')

    @classmethod
    def get(cls):
        if cls.objects.all().count() > 1:
            raise Exception('Should not have multiple settings records')
        return cls.objects.get()

    def get_tmdb_poster_url(self, poster_path):
        return os.path.join(
            self.tmdb_configuration['images']['secure_base_url'],
            'original',
            poster_path.lstrip('/'),
        )

    def should_save_subtitles(self):
        return all([
            self.open_subtitles_auto,
            self.open_subtitles_user_token,
        ])


class WatchMediaBase(models.Model):
    """
    Abstract base class for all watchable media classes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    collected = models.BooleanField(default=False)
    collected_date = models.DateTimeField(blank=True, null=True)
    download_path = models.CharField(max_length=1000, blank=True, null=True, unique=True)
    last_attempt_date = models.DateTimeField(blank=True, null=True)
    transmission_torrent_hash = models.CharField(max_length=100, null=True, blank=True)
    transmission_torrent_name = models.CharField(max_length=1000, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)

    def abs_download_path(self):
        return os.path.join(settings.INTERNAL_DOWNLOAD_PATH, self.download_path)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['collected']),
            models.Index(fields=['collected_date']),
            models.Index(fields=['date_updated']),
        ]


class WatchMovie(WatchMediaBase):
    tmdb_movie_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    poster_image_url = models.CharField(max_length=1000)
    quality_profile_custom = models.CharField(max_length=500, null=True, blank=True, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))

    class Meta:
        ordering = ('name',)
        permissions = (
            (PERM_CAN_WATCH_IMMEDIATELY_MOVIE, 'Can immediately start watching movies'),
        )

    def __str__(self):
        return self.name


class WatchTVShow(models.Model):
    """
    Shows are unique in that you don't request to "watch" a show.  Instead, you watch specific seasons and episodes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tmdb_show_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    poster_image_url = models.CharField(max_length=1000)
    release_date = models.DateField(null=True, blank=True)
    auto_watch = models.BooleanField(default=False)  # whether to automatically watch future seasons
    auto_watch_date_updated = models.DateField(null=True, blank=True)  # date auto watch requested/updated
    quality_profile_custom = models.CharField(max_length=500, null=True, blank=True, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))

    class Meta:
        ordering = ('name',)
        permissions = (
            (PERM_CAN_WATCH_IMMEDIATELY_TV, 'Can immediately start watching tv shows'),
        )

    def __str__(self):
        return self.name


class WatchTVSeasonRequest(models.Model):
    """
    This is a special model for keeping track of a user's request to watch a TV Season.
    Nefarious is at the mercy of the data provider (TMDB) which doesn't always have the full episode list at the time of the request.
    TMDB sometimes only adds listings for episodes as they are published.
    The task queue will routinely scan for new episodes for a season that may not have had it's full episode list at the time of
    the request to watch the entire season.  Essentially, nefarious will re-request a season's episode list to see if it needs to download any new episodes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    watch_tv_show = models.ForeignKey(WatchTVShow, on_delete=models.CASCADE)
    season_number = models.IntegerField()
    quality_profile_custom = models.CharField(max_length=500, null=True, blank=True, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))
    collected = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    release_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('watch_tv_show', 'season_number',)
        indexes = [
            models.Index(fields=['collected']),
        ]

    def __str__(self):
        return '{} - Season {:02d}'.format(self.watch_tv_show, self.season_number)


class WatchTVSeason(WatchMediaBase):
    watch_tv_show = models.ForeignKey(WatchTVShow, on_delete=models.CASCADE)
    season_number = models.IntegerField()

    class Meta:
        unique_together = ('watch_tv_show', 'season_number',)
        indexes = [
            models.Index(fields=['season_number']),
        ]

    def __str__(self):
        return '{} - Season {:02d}'.format(self.watch_tv_show, self.season_number)

    @property
    def name(self):
        return str(self)


class WatchTVEpisode(WatchMediaBase):
    watch_tv_show = models.ForeignKey(WatchTVShow, on_delete=models.CASCADE)
    tmdb_episode_id = models.IntegerField(unique=True)
    season_number = models.IntegerField()
    episode_number = models.IntegerField()

    class Meta:
        unique_together = ('watch_tv_show', 'season_number', 'episode_number')
        indexes = [
            models.Index(fields=['season_number']),
            models.Index(fields=['episode_number']),
        ]

    def __str__(self):
        # i.e "Broad City - S01E04"
        return '{} - S{:02d}E{:02d}'.format(self.watch_tv_show, self.season_number, self.episode_number)

    @property
    def name(self):
        return str(self)


class TorrentBlacklist(models.Model):
    hash = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return '{}: {}'.format(self.name or '<unknown>', self.hash)
