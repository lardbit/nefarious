from django.contrib import admin
from nefarious.models import (
    NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, TorrentBlacklist, WatchTVSeason, WatchTVSeasonRequest,
)


@admin.register(NefariousSettings)
class SettingsAdmin(admin.ModelAdmin):
    pass


@admin.register(TorrentBlacklist)
class BlacklistAdmin(admin.ModelAdmin):
    pass


class WatchTVEpisodeInline(admin.TabularInline):
    model = WatchTVEpisode


class WatchTVSeasonInline(admin.TabularInline):
    show_change_link = True
    model = WatchTVSeason


@admin.register(WatchTVShow)
class TVShowAdmin(admin.ModelAdmin):
    list_filter = ('user',)
    list_display = ('name', 'user',)
    inlines = (
        WatchTVEpisodeInline,
        WatchTVSeasonInline,
    )


@admin.register(WatchTVEpisode)
class TVEpisodeAdmin(admin.ModelAdmin):
    list_filter = ('user', 'watch_tv_show',)
    list_display = ('name', 'watch_tv_show', 'user',)


@admin.register(WatchMovie, WatchTVSeason)
class MediaAdmin(admin.ModelAdmin):
    list_filter = ('user',)
    list_display = ('name', 'user',)


@admin.register(WatchTVSeasonRequest)
class WatchTVSeasonRequestAdmin(admin.ModelAdmin):
    pass
