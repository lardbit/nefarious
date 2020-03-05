import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import * as _ from 'lodash';
import { forkJoin, Observable } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { NgbTabset } from '@ng-bootstrap/ng-bootstrap';


@Component({
  selector: 'app-media-tv',
  templateUrl: './media-t-v.component.html',
  styleUrls: ['./media-t-v.component.css']
})
export class MediaTVComponent implements OnInit {
  @ViewChild('tabsetEl') tabsetEl: NgbTabset;
  public result: any;
  public isManuallySearching = false;
  public isManualSearchEnabled = false;
  public watchEpisodesOptions: {
    [param: number]: boolean,
  };
  public manualSearchTmdbSeason: any;
  public manualSearchTmdbEpisode: any;
  public isLoading = true;
  public isSaving = false;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private toastr: ToastrService,
    ) {
  }

  ngOnInit() {
    const routeParams = this.route.snapshot.params;
    this.apiService.searchMediaDetail(this.apiService.SEARCH_MEDIA_TYPE_TV, routeParams.id).subscribe(
      (data) => {
        this.result = data;
        this._buildWatchOptions();
        this.isLoading = false;
      },
      (error) => {
        this.toastr.error('An unknown error occurred');
      }
    );

    // watch for updated media
    this.apiService.mediaUpdated$.subscribe(
      () => {
        this._buildWatchOptions();
      }
    );
  }

  public submitForSeason(seasonNumber: number) {

    // watch show if not already
    if (!this.isWatchingShow()) {
      console.log('not already watching show %s', this.result.id);
      this._watchShow().subscribe(
        (data) => {
          this._watchEpisodesForSeason(seasonNumber);
        },
      );
    } else {
      this._watchEpisodesForSeason(seasonNumber);
    }
  }

  public mediaPosterURL(result) {
    return `${this.apiService.settings.tmdb_configuration.images.base_url}/original/${result.poster_path}`;
  }

  public watchAllSeasons() {

    if (!this.isWatchingShow()) {
      this._watchShow().subscribe(
        (data) => {
          this.watchAllSeasons();
        }
      );
    } else {
        for (const season of this.result.seasons) {
          this.watchEntireSeason(season);
        }
    }
  }

  public watchEntireSeason(season) {

    this.isSaving = true;

    if (!this.isWatchingShow()) {
      this._watchShow().subscribe(
        (data) => {
          this.watchEntireSeason(season);
        }
      );
    } else {

        const watchTvShow = this._getWatchShow();

        this.apiService.watchTVSeason(watchTvShow.id, season.season_number).subscribe(
          (data) => {
            this.isSaving = false;
            this.toastr.success(`Watching season ${season.season_number}`);
            this._buildWatchOptions();
          },
          (error) => {
            this.isSaving = false;
            this.toastr.error('An unknown error occurred');
            console.log(error);
          }
        );
    }
  }

  public userIsStaff(): boolean {
    return this.apiService.userIsStaff();
  }

  public stopWatchingShow() {
    const watchShow = this._getWatchShow();
    if (watchShow) {
      this.apiService.unWatchTVShow(watchShow.id).subscribe(
        (data) => {
          this.toastr.success('Stopped watching show');
          this._buildWatchOptions();
        },
        (error) => {
          this.toastr.error('An unknown error occurred');
        }
      );
    }
  }

  public getWatchMedia() {
    return this._getWatchShow();
  }

  public isWatchingAllSeasons() {
    for (const season of this.result.seasons) {
      if (!this.isWatchingSeason(season.season_number)) {
        return false;
      }
    }
    return true;
  }

  public isWatchingSeason(seasonNumber: number) {
    const watchSeasonRequest = this._getWatchSeasonRequest(seasonNumber);
    return Boolean(watchSeasonRequest);
  }

  public hasCollectedAllEpisodesInSeason(season: any) {
    // watching entire season
    if (this.hasCollectedSeason(season)) {
      return true;
    }

    // verify every episode is collected
    for (const episode of season.episodes) {
      const watchEpisode = this._getWatchEpisode(episode.id);
      if (!watchEpisode || !watchEpisode.collected) {
        return false;
      }
    }
    return true;
  }

  public isWatchingAllEpisodesInSeason(season: any) {
    // watching all episodes in season
    let watchingEpisodes = 0;
    for (const episode of season.episodes) {
      if (this.isWatchingEpisode(episode.id)) {
        watchingEpisodes += 1;
      }
    }
    return season.episodes.length === watchingEpisodes;
  }

  public isWatchingAnyEpisodeInSeason(season: any) {
    for (const episode of season.episodes) {
      if (this.isWatchingEpisode(episode.id)) {
        return true;
      }
    }
    return false;
  }

  public hasCollectedSeason(season): boolean {
    const watchSeason = this._getWatchSeason(season.season_number);
    return watchSeason && watchSeason.collected;
  }

  public stopWatchingEntireSeason(season: any) {
    const watchSeasonRequest = this._getWatchSeasonRequest(season.season_number);
    if (watchSeasonRequest) {
        this.apiService.unWatchTVSeason(watchSeasonRequest.id).subscribe(
          (data) => {
            this.toastr.success(`Stopped watching ${this.result.name} - Season ${watchSeasonRequest.season_number}`);
            this._buildWatchOptions();
          },
          (error) => {
            console.error(error);
            this.toastr.error('An unknown error occurred');
          }
        );
    }
  }

  public isWatchingShow() {
    return Boolean(this._getWatchShow());
  }

  public manuallySearchSeason(season: any) {
    this.manualSearchTmdbSeason = season;
    this.isManuallySearching = true;
    this.tabsetEl.select('manual-search-tab');
  }

  public manuallySearchEpisode(season: any, episode: any) {
    this.manualSearchTmdbSeason = season;
    this.manualSearchTmdbEpisode = episode;
    this.isManuallySearching = true;
    this.tabsetEl.select('manual-search-tab');
  }

  public manuallyDownloadComplete() {
    this.isManuallySearching = false;
    this.tabsetEl.select('main-tab');
    this._buildWatchOptions();
  }

  public canUnWatchSeason(seasonNumber: number) {
    const watchSeasonRequest = this._getWatchSeasonRequest(seasonNumber);
    return this.userIsStaff() || (watchSeasonRequest && watchSeasonRequest.requested_by === this.apiService.user.username);
  }

  public canUnWatchShow() {
    const watchShow = this._getWatchShow();
    return this.userIsStaff() || (watchShow && watchShow.requested_by === this.apiService.user.username);
  }

  public canUnWatchEpisode(episodeId) {
    const watchEpisode = this._getWatchEpisode(episodeId);
    return this.userIsStaff() || (watchEpisode && watchEpisode.requested_by === this.apiService.user.username);
  }

  public isWatchingEpisode(episodeId): Boolean {
    return Boolean(_.find(this.apiService.watchTVEpisodes, (watching) => {
      return watching.tmdb_episode_id === episodeId;
    }));
  }

  protected _watchShow(): Observable<any> {
    return this.apiService.watchTVShow(this.result.id, this.result.name, this.mediaPosterURL(this.result), this.result.first_air_date).pipe(
      tap((data) => {
        this.toastr.success(`Watching show ${data.name}`);
      }),
      catchError((error) => {
        this.toastr.error('An unknown error occurred');
        throw error;
      }),
    );
  }

  protected _getWatchSeasonRequest(seasonNumber: number) {
    const watchShow = this._getWatchShow();
    if (watchShow) {
      return _.find(this.apiService.watchTVSeasonRequests, (watchSeasonRequest) => {
        return watchSeasonRequest.watch_tv_show === watchShow.id && watchSeasonRequest.season_number === seasonNumber;
      });
    }
    return null;
  }

  protected _getWatchSeason(seasonNumber: number) {
    const watchShow = this._getWatchShow();
    if (watchShow) {
      return _.find(this.apiService.watchTVSeasons, (watchSeason) => {
        return watchSeason.watch_tv_show === watchShow.id && watchSeason.season_number === seasonNumber;
      });
    }
    return null;
  }

  protected _buildWatchOptions() {
    const watchingOptions: any = {};
    for (const season of this.result.seasons) {
      for (const episode of season.episodes) {
        watchingOptions[episode.id] = this.isWatchingEpisode(episode.id) || this.isWatchingSeason(season.season_number);
      }
    }
    this.watchEpisodesOptions = watchingOptions;
  }

  protected _getWatchEpisode(episodeId) {
    return _.find(this.apiService.watchTVEpisodes, (watch) => {
      return watch.tmdb_episode_id === episodeId;
    });
  }

  protected _getSeasonFromEpisodeId(episodeId) {
    let result = null;
    _.each(this.result.seasons, (season) => {
      _.each(season.episodes, (episode) => {
        if (episode.id === episodeId) {
          result = season;
          return;
        }
      });
    });
    return result;
  }

  protected _getEpisode(episodeId) {
    let result = null;
    _.each(this.result.seasons, (season) => {
      _.each(season.episodes, (episode) => {
        if (episode.id === episodeId) {
          result = episode;
          return;
        }
      });
    });
    return result;
  }

  protected _getWatchShow() {
    return _.find(this.apiService.watchTVShows, (watchShow) => {
      return watchShow.tmdb_show_id === this.result.id;
    });
  }

  protected _watchEpisodesForSeason(seasonNumber: number) {

    const observables = [];

    _.forOwn(this.watchEpisodesOptions, (shouldWatch: boolean, episodeIdString: string) => {
      const episodeId = Number(episodeIdString);
      const episode = this._getEpisode(episodeId);

      // requested to watch
      if (shouldWatch) {
        // make sure the episode is for the supplied season and they're not already watching it
        if (seasonNumber === episode.season_number && !this.isWatchingEpisode(episodeId)) {
          const season = this._getSeasonFromEpisodeId(episodeId);
          const watchShow = this._getWatchShow();
          if (episode && season && watchShow) {
            observables.push(
              this.apiService.watchTVEpisode(
                watchShow.id, Number(episodeId), episode.season_number, episode.episode_number));
          } else {
            console.log('ERROR: episode %s not found in results', episodeId);
          }
        }
      } else { // stop watching
        if (this.isWatchingEpisode(episodeId)) {
          const watch = this._getWatchEpisode(episodeId);
          observables.push(this.apiService.unWatchTVEpisode(watch.id));
        }
      }
    });

    // run any updates
    if (observables.length) {
      this.isSaving = true;
      forkJoin(observables).subscribe(
        (data) => {
          this.isSaving = false;
          this.toastr.success('Saved');
        },
        (error) => {
          this.isSaving = false;
          this.toastr.error('An unknown error occurred');
        },
        () => {
          this._buildWatchOptions();
        }
      );
    }

  }
}
