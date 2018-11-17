from django.contrib import admin
from nefarious.models import NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, TorrentBlacklist


@admin.register(NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, TorrentBlacklist, )
class Admin(admin.ModelAdmin):
    pass
