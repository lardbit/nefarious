import { Component, OnInit, Input, OnDestroy } from '@angular/core';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import { interval, Observable } from 'rxjs';
import { throttle } from 'rxjs/operators';
import * as _ from 'lodash';

const POLL_TIME = 5000;


@Component({
  selector: 'app-torrent-details',
  templateUrl: './torrent-details.component.html',
  styleUrls: ['./torrent-details.component.css']
})
export class TorrentDetailsComponent implements OnInit, OnDestroy {
  @Input() watchMedia: any;
  @Input() mediaType: string;
  public isSaving = false;
  public isFetchingInitialTorrents = true;
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

    this._fetchTorrents().subscribe(
      (data) => {
        this._fetchTorrentsSuccess(data);

        // fetch torrent details on an interval
        this._torrentFetchInterval = interval(POLL_TIME).pipe(
          throttle(() => interval(POLL_TIME))
        ).subscribe(
          () => {
            this._fetchTorrents().subscribe(
              (data_) => {
                this._fetchTorrentsSuccess(data_);
              },
              (error) => {
                this._fetchTorrentsFailure(error);
              }
            );
          });
      },
      (error) => {
        this._fetchTorrentsFailure(error);
      }
    );
  }

  public blacklistRetry(watchMedia, blacklist?: boolean) {
    const message = blacklist ? 'Blacklisting torrent and retrying' : 'Retrying download now';
    this.isSaving = true;

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

    // remove blacklisted watch media
    this.results = this.results.filter((result) => {
      return result.watchMedia.id !== watchMedia.id;
    });

    endpoint.subscribe(
      (data) => {
        this.isSaving = false;
        this.toastr.success(message);
      },
      (error) => {
        console.error(error);
        this.isSaving = false;
        this.toastr.error('An unknown error occurred');
      }
    );

  }

  public resultTrackBy(index, result) {
    return result.watchMedia.id;
  }

  protected _fetchTorrents(): Observable<any> {
    this.isFetchingInitialTorrents = false;

    const params = {
      watch_movies: [],
      watch_tv_shows: [],
    };

    // update media instances and build torrent params

    // tv
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      params.watch_tv_shows.push(this.watchMedia.id);
    } else {  // movie
      params.watch_movies.push(this.watchMedia.id);
    }

    params.watch_movies = _.uniq(params.watch_movies);
    params.watch_tv_shows = _.uniq(params.watch_tv_shows);

    return this.apiService.fetchCurrentTorrents(params);
  }

  protected _fetchTorrentsSuccess(data: any) {
    this.results = data.sort((a: any, b: any) => {
      if (a.watchMedia.name < b.watchMedia.name) {
        return -1;
      }
      if (a.watchMedia.name > b.watchMedia.name) {
        return 1;
      }
      return 0;
    });
  }

  protected _fetchTorrentsFailure(error) {
    console.error(error);
  }
}
