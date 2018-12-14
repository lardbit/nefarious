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
        WatchTVSeasonInline,
    )


@admin.register(WatchTVSeason)
class TVSeasonAdmin(admin.ModelAdmin):
    inlines = (
        WatchTVEpisodeInline,
    )


@admin.register(NefariousSettings, WatchTVEpisode, WatchMovie, TorrentBlacklist)
class Admin(admin.ModelAdmin):
    pass
