import { NgZone } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { ColumnMode } from '@swimlane/ngx-datatable';
import { DatePipe } from '@angular/common';
import { MediaFilterPipe } from '../filter.pipe';
import * as moment from 'moment';

// statuses considered stalled (transmission-rpc status strings)
const STALLED_STATUSES = ['stopped', 'idle', 'check pending', 'checking'];
// hours without torrent activity before a download is considered stalled
const STALLED_HOURS = 24;

export interface MediaStatus {
  key: string;
  label: string;
  css: string;
}

@Component({
  selector: 'app-wanted',
  templateUrl: './wanted.component.html',
  styleUrls: ['./wanted.component.css'],
  providers: [DatePipe],
})
export class WantedComponent implements OnInit, OnDestroy {
  public results: any[] = [];
  public sortBy: {prop: string, dir: string}[] = [
    { prop: 'date_added', dir: 'desc', },
  ];
  public mediaType: string;
  public search = '';
  public ColumnMode = ColumnMode;
  // live torrent state keyed by watch media id
  public torrentByMediaId: {[id: number]: any} = {};
  public torrentsLoaded = false;
  public retrying: {[id: number]: boolean} = {};

  protected _changes: Subscription;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private route: ActivatedRoute,
    private ngZone: NgZone,
    private datePipe: DatePipe,
    private mediaFilter: MediaFilterPipe,
  ) {}

  ngOnInit() {

    // watch for updated media
    this._changes = this.apiService.mediaUpdated$.subscribe(
      () => {
        this.ngZone.run(() => {
          this._buildResults(this.mediaType);
        });
      }
    );

    this.route.params.subscribe(
      (params) => {
        this._buildResults(params.type);
      }
    );
  }

  ngOnDestroy() {
    this._changes.unsubscribe();
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }

  get rows() {

    // format dates
    this.results.forEach((result) => {
      ['release_date', 'date_added', 'last_attempt_date'].forEach((dateKey) => {
        if (result[dateKey]) {
          result[dateKey] = this.datePipe.transform(result[dateKey], 'yyyy-MM-dd');
        }
      });
    });

    // filter by search query
    if (this.search) {
      return this.mediaFilter.transform(this.results, this.search);
    }

    return this.results;
  }

  protected _buildResults(mediaType: string) {
    this.results = [];
    this.mediaType = mediaType;
    let wanted: any[];
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      wanted = this.apiService.watchTVSeasons.concat(this.apiService.watchTVEpisodes);
    } else {
      wanted = this.apiService.watchMovies;
    }
    this.results = wanted.filter((watchMedia) => {
      return !watchMedia.collected;
    });
    this._fetchTorrents();
  }

  // fetch live torrent state for the wanted items to detect stalled downloads
  protected _fetchTorrents() {
    this.torrentsLoaded = false;
    if (!this.results.length) {
      this.torrentByMediaId = {};
      this.torrentsLoaded = true;
      return;
    }

    const params: any = {};
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      // wanted rows are seasons/episodes; the endpoint expects show ids
      const showIds = Array.from(new Set(
        this.results.map((row) => row.watch_tv_show).filter((id) => id != null)
      ));
      params.watch_tv_shows = showIds;
    } else {
      params.watch_movies = this.results.map((row) => row.id);
    }

    this.apiService.fetchCurrentTorrents(params).subscribe(
      (data: any[]) => {
        const map: {[id: number]: any} = {};
        (data || []).forEach((result) => {
          if (result.torrent && result.watchMedia) {
            map[result.watchMedia.id] = result.torrent;
          }
        });
        this.torrentByMediaId = map;
        this.torrentsLoaded = true;
      },
      (error) => {
        console.error(error);
        this.torrentByMediaId = {};
        this.torrentsLoaded = true;
      }
    );
  }

  public statusOf(row: any): MediaStatus {
    if (this._isReleaseInFuture(row)) {
      return {key: 'not_released', label: 'Not released', css: 'secondary'};
    }
    const torrent = this.torrentByMediaId[row.id];
    if (torrent) {
      if (torrent.progress >= 100) {
        return {key: 'downloading', label: 'Finishing', css: 'info'};
      }
      if (this._isStalled(torrent)) {
        return {key: 'stalled', label: 'Stalled', css: 'warning'};
      }
      return {key: 'downloading', label: `Downloading ${torrent.progress}%`, css: 'info'};
    }
    // no active torrent
    if (!this.torrentsLoaded) {
      return {key: 'queued', label: 'Queued', css: 'secondary'};
    }
    if (row.last_attempt_date) {
      return {key: 'no_match', label: 'No match found', css: 'danger'};
    }
    return {key: 'queued', label: 'Queued', css: 'secondary'};
  }

  public canRetry(row: any): boolean {
    const status = this.statusOf(row).key;
    return status === 'no_match' || status === 'stalled';
  }

  public retry(row: any) {
    this.retrying[row.id] = true;
    let endpoint;
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE) {
      endpoint = this.apiService.blacklistRetryMovie(row.id);
    } else if (row.tmdb_episode_id) {
      endpoint = this.apiService.blacklistRetryTVEpisode(row.id);
    } else {
      endpoint = this.apiService.blacklistRetryTVSeason(row.id);
    }
    endpoint.subscribe(
      () => {
        this.retrying[row.id] = false;
        this.toastr.success('Retrying download');
        this._fetchTorrents();
      },
      (error) => {
        console.error(error);
        this.retrying[row.id] = false;
        this.toastr.error('An error occurred retrying the download');
      }
    );
  }

  protected _isStalled(torrent: any): boolean {
    if (STALLED_STATUSES.includes((torrent.status || '').toLowerCase())) {
      return true;
    }
    if (torrent.date_active) {
      return moment().diff(moment(torrent.date_active), 'hours') >= STALLED_HOURS;
    }
    return false;
  }

  protected _isReleaseInFuture(row: any): boolean {
    if (!row.release_date) {
      return false;
    }
    const releaseDate = moment(row.release_date);
    return releaseDate.isValid() && releaseDate.isAfter(moment(), 'day');
  }
}
