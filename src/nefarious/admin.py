from django.contrib import admin
from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, TorrentBlacklist, WatchTVSeason
)


class WatchTVEpisodeInline(admin.TabularInline):
    model = WatchTVEpisode


@admin.register(WatchTVShow)
class TVShowAdmin(admin.ModelAdmin):
    inlines = (
        WatchTVEpisodeInline,
    )


@admin.register(NefariousSettings, WatchTVEpisode, WatchMovie, TorrentBlacklist, WatchTVSeason)
class Admin(admin.ModelAdmin):
    pass
