import { Component, OnInit, Input, OnDestroy } from '@angular/core';
import { ApiService } from '../api.service';
import { interval } from 'rxjs';
import { throttle } from 'rxjs/operators';
import * as _ from 'lodash';

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
  public POLL_TIME = 5000;
  public results: {
    watchMedia: any,
    torrent: any,
  }[] = [];

  protected _torrentFetchInterval: any;

  constructor(
    private apiService: ApiService,
  ) {}

  ngOnDestroy() {
    // stop polling for torrent details
    if (this._torrentFetchInterval && !this._torrentFetchInterval.isStopped) {
      this._torrentFetchInterval.unsubscribe();
    }
  }

  ngOnInit() {
    // fetch torrent details on an interval
    this._torrentFetchInterval = interval(this.POLL_TIME).pipe(
      throttle(() => interval(this.POLL_TIME))
    ).subscribe(
      () => {
        this._fetchTorrents();
      });
  }

  public getWatchMediaFromTorrentId(id) {
    return _.filter(this.watchMedia, (media) => {
      return media.transmission_torrent_id === id;
    });
  }

  public getTorrentIds() {
    return this.watchMedia
      .filter((v) => v.transmission_torrent_id)
      .map((v) => v.transmission_torrent_id);
  }

  public blacklistRetry(torrent) {
    this.isSaving = true;
    const watchMediaList = this.getWatchMediaFromTorrentId(torrent.id);

    watchMediaList.forEach((watchMedia) => {

      const endpoint = this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE ?
        this.apiService.blacklistRetryMovie(watchMedia.id) :
        this.apiService.blacklistRetryTV(watchMedia.id);

      endpoint.subscribe(
        (data) => {
          this.isSaving = false;

          // filter the watch media/torrent results since it was updated
          this.results = _.filter(this.results, (result) => {
            return result.watchMedia.id === watchMedia.id;
          })
        },
        (error) => {
          console.error(error);
          this.isSaving = false;
        }
      );

    })
  }

  protected _fetchTorrents() {
    const transmission_torrent_ids = this.getTorrentIds();

    for (const watchMedia of this.watchMedia) {
      // fetch watch instance if there's no torrent id populated yet
      if (!watchMedia.transmission_torrent_id) {
        // type tv episode
        if (watchMedia.tmdb_episode_id) {
          this.apiService.fetchWatchTVEpisode(watchMedia.id).subscribe();
        } else { // type movie
          this.apiService.fetchWatchMovie(watchMedia.id).subscribe();
        }
      }
    }

    if (transmission_torrent_ids.length === 0) {
      console.log('no transmission ids yet');
      return;
    }

    this.apiService.fetchCurrentTorrents(transmission_torrent_ids).subscribe(
      (data) => {
        this.torrents = data;
        this.results = this.watchMedia.map((watchMedia) => {
          return {
            watchMedia: watchMedia,
            torrent: _.find(this.torrents, (torrent) => {
              return torrent.id === watchMedia.transmission_torrent_id;
            }),
          };
        });
      },
      (error) => {
        console.error(error);
      }
    );
  }

}
