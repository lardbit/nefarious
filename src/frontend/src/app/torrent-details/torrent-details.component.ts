import { Component, OnInit, Input, OnDestroy } from '@angular/core';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import { interval } from 'rxjs';
import { throttle } from 'rxjs/operators';
import * as _ from 'lodash';

const POLL_TIME = 5000;

@Component({
  selector: 'app-torrent-details',
  templateUrl: './torrent-details.component.html',
  styleUrls: ['./torrent-details.component.css']
})
export class TorrentDetailsComponent implements OnInit, OnDestroy {
  @Input() watchMedia: any[];
  @Input() mediaType: string;
  public torrents: any[] = [];
  public isSaving = false;
  public results: {
    watchMedia: any,
    torrent: any,
  }[] = [];

  protected _torrentFetchInterval: any;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
  ) {}

  ngOnDestroy() {
    // stop polling for torrent details
    if (this._torrentFetchInterval && !this._torrentFetchInterval.isStopped) {
      this._torrentFetchInterval.unsubscribe();
    }
  }

  ngOnInit() {
    this._updateResults();

    // fetch torrent details on an interval
    this._torrentFetchInterval = interval(POLL_TIME).pipe(
      throttle(() => interval(POLL_TIME))
    ).subscribe(
      () => {
        this._fetchTorrents();
      });
  }

  public getWatchMediaFromTorrent(torrent) {
    return _.filter(this.watchMedia, (media) => {
      return media.transmission_torrent_hash === torrent.hashString;
    });
  }

  public blacklistRetry(torrent) {
    this.isSaving = true;
    const watchMediaList = this.getWatchMediaFromTorrent(torrent);

    watchMediaList.forEach((watchMedia) => {

      let endpoint;
      if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE) {
        endpoint = this.apiService.blacklistRetryMovie(watchMedia.id);
      } else {
        if (watchMedia.tmdb_episode_id) {
          endpoint = this.apiService.blacklistRetryTVEpisode(watchMedia.id);
        } else {
          endpoint = this.apiService.blacklistRetryTVSeason(watchMedia.id);
        }
      }

      endpoint.subscribe(
        (data) => {
          this.isSaving = false;

          // filter the watch media/torrent results since it was updated
          this.results = _.filter(this.results, (result) => {
            return result.watchMedia.id === watchMedia.id;
          });
          this.toastr.success('Successfully blacklisted');
        },
        (error) => {
          console.error(error);
          this.isSaving = false;
          this.toastr.error('An unknown error occurred');
        }
      );

    });
  }

  protected _updateResults() {
    this.results = this.watchMedia.map((watchMedia) => {
      return {
        watchMedia: watchMedia,
        torrent: _.find(this.torrents, (torrent) => {
          return torrent.hashString === watchMedia.transmission_torrent_hash;
        }),
      };
    });
  }

  protected _fetchTorrents() {
    const params = {
      watch_movies: [],
      watch_tv_episodes: [],
      watch_tv_seasons: [],
    };

    // update media instances and build torrent params
    for (const watchMedia of this.watchMedia) {
      // type tv
      if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
        // type tv episode
        if (watchMedia.tmdb_episode_id) {
          this.apiService.fetchWatchTVEpisode(watchMedia.id).subscribe();
          params.watch_tv_episodes.push(watchMedia.id);
        } else {  // type tv season
          this.apiService.fetchWatchTVSeason(watchMedia.id).subscribe();
          params.watch_tv_seasons.push(watchMedia.id);
        }
      } else {
        // fetch media if there's no torrent details yet
        this.apiService.fetchWatchMovie(watchMedia.id).subscribe();
        params.watch_movies.push(watchMedia.id);
      }
    }

    this.apiService.fetchCurrentTorrents(params).subscribe(
      (data) => {
        this.torrents = data;
        this._updateResults();
      },
      (error) => {
        console.error(error);
      }
    );
  }

}
