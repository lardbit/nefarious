from django.contrib import admin
from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, TorrentBlacklist, WatchTVSeason
)


class WatchTVEpisodeInline(admin.TabularInline):
    model = WatchTVEpisode


class WatchTVSeasonInline(admin.TabularInline):
    show_change_link = True
    model = WatchTVSeason


@admin.register(WatchTVShow)
class TVShowAdmin(admin.ModelAdmin):
    inlines = (
        WatchTVEpisodeInline,
        WatchTVSeasonInline,
    )


@admin.register(NefariousSettings, WatchTVSeason, WatchTVEpisode, WatchMovie, TorrentBlacklist)
class Admin(admin.ModelAdmin):
    pass
