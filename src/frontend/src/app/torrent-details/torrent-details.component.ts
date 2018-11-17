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
  public torrents: any[] = [];
  public isSaving = false;

  protected POLL_TIME = 5000;
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
    return _.find(this.watchMedia, (media) => {
      return media.transmission_torrent_id === id;
    });
  }

  public getTorrentIds() {
    return this.watchMedia.filter((v) => v.transmission_torrent_id).map((v) => v.transmission_torrent_id);
  }

  public blacklistRetry(torrent) {
    this.isSaving = true;
    const watchMedia = this.getWatchMediaFromTorrentId(torrent.id);
    this.apiService.blacklistRetryMovie(watchMedia.id).subscribe(
      (data) => {
        console.log(data);
        this.isSaving = false;
      },
      (error) => {
        console.error(error);
        this.isSaving = false;
      }
    );
  }

  protected _fetchTorrents() {
    const transmission_torrent_ids = this.getTorrentIds();

    for (const watchMedia of this.watchMedia) {
      if (!watchMedia.transmission_torrent_id) {
        // type tv show
        if (watchMedia.tmdb_show_id) {
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
      },
      (error) => {
        console.error(error);
      }
    );
  }

}
