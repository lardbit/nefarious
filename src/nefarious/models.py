import os
from django.contrib.auth.models import User
from django.conf import settings
from jsonfield import JSONField
from django.db import models
from nefarious import quality

PERM_CAN_WATCH_IMMEDIATELY_TV = 'can_immediately_watch_tv'
PERM_CAN_WATCH_IMMEDIATELY_MOVIE = 'can_immediately_watch_movie'


class NefariousSettings(models.Model):
    JACKETT_TOKEN_DEFAULT = 'COPY_YOUR_JACKETT_TOKEN_HERE'

    language = models.CharField(max_length=2, default='en')  # chosen language

    jackett_host = models.CharField(max_length=500, default='jackett')
    jackett_port = models.IntegerField(default=9117)
    jackett_token = models.CharField(max_length=500, default=JACKETT_TOKEN_DEFAULT)

    transmission_host = models.CharField(max_length=500, default='transmission')
    transmission_port = models.IntegerField(default=9091)
    transmission_user = models.CharField(max_length=500, blank=True, default='')  # credentials aren't required for transmission
    transmission_pass = models.CharField(max_length=500, blank=True, default='')  # credentials aren't required for transmission
    transmission_tv_download_dir = models.CharField(max_length=500, default='tv/', help_text='Relative to download path')
    transmission_movie_download_dir = models.CharField(max_length=500, default='movies/', help_text='Relative to download path')

    tmdb_token = models.CharField(max_length=500, default=settings.TMDB_API_TOKEN)
    tmdb_configuration = JSONField(blank=True, null=True)
    tmdb_languages = JSONField(blank=True, null=True)  # type: list

    quality_profile_tv = models.CharField(max_length=500, default=quality.PROFILE_ANY.name, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))
    quality_profile_movies = models.CharField(max_length=500, default=quality.PROFILE_HD_720P_1080P.name, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))

    allow_hardcoded_subs = models.BooleanField(default=False)

    # expects keyword/boolean pairs like {"x265": false, "265": false}
    keyword_search_filters = JSONField(blank=True, null=True)  # type: dict

    # webhook
    webhook_url = models.CharField(max_length=1500, blank=True, null=True)  # url of webhook
    webhook_key = models.CharField(max_length=50, blank=True, default='text')  # data key to post, i.e "text"

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


class WatchMediaBase(models.Model):
    """
    Abstract base class for all watchable media classes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quality_profile_custom = models.CharField(max_length=500, blank=True, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))
    date_added = models.DateTimeField(auto_now_add=True)
    collected = models.BooleanField(default=False)
    collected_date = models.DateTimeField(blank=True, null=True)
    last_attempt_date = models.DateTimeField(blank=True, null=True)
    transmission_torrent_hash = models.CharField(max_length=100, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)

    class Meta:
        abstract = True


class WatchMovie(WatchMediaBase):
    tmdb_movie_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    poster_image_url = models.CharField(max_length=1000)

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
    quality_profile_custom = models.CharField(max_length=500, blank=True, choices=zip(quality.PROFILE_NAMES, quality.PROFILE_NAMES))
    collected = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    release_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('watch_tv_show', 'season_number',)

    def __str__(self):
        return '{} - Season {:02d}'.format(self.watch_tv_show, self.season_number)


class WatchTVSeason(WatchMediaBase):
    watch_tv_show = models.ForeignKey(WatchTVShow, on_delete=models.CASCADE)
    season_number = models.IntegerField()

    class Meta:
        unique_together = ('watch_tv_show', 'season_number',)

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

    def __str__(self):
        # i.e "Broad City - S01E04"
        return '{} - S{:02d}E{:02d}'.format(self.watch_tv_show, self.season_number, self.episode_number)

    @property
    def name(self):
        return str(self)


class TorrentBlacklist(models.Model):
    hash = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.hash
