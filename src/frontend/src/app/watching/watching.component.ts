import { NgZone } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { Subscription } from 'rxjs';
import { MediaFilterPipe } from '../filter.pipe';
import { ColumnMode } from '@swimlane/ngx-datatable';
import { DatePipe } from '@angular/common';


@Component({
  selector: 'app-watching',
  templateUrl: './watching.component.html',
  styleUrls: ['./watching.component.scss'],
  providers: [DatePipe],
})
export class WatchingComponent implements OnInit, OnDestroy {
  public results: any[] = [];
  public mediaType: string;
  public search: string;
  public ColumnMode = ColumnMode;

  protected _changes: Subscription;

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private mediaFilter: MediaFilterPipe,
    private datePipe: DatePipe,
    private ngZone: NgZone,
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

    // watch for route changes
    this.route.params.subscribe(
      (params) => {
        this.mediaType = params.type;
        this._buildResults(this.mediaType);
      }
    );
  }

  ngOnDestroy() {
    this._changes.unsubscribe();
  }

  get rows() {

    // calculate tv "collected date" by last season/episode collected_date since shows don't have one
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      this.results = this.results.map((watchShow) => {
        return {collected_date: this.lastTVDownloadActivityDate(watchShow), ...watchShow};
      });
    }
    // format dates
    this.results.forEach((result) => {
      if (result.collected_date) {
        result.collected_date = this.datePipe.transform(result.collected_date, 'yyyy-MM-dd');
      }
      if (result.date_added) {
        result.date_added = this.datePipe.transform(result.date_added, 'yyyy-MM-dd');
      }
    });

    // filter by search query
    if (this.search) {
      return this.mediaFilter.transform(this.results, this.search);
    }

    return this.results;
  }

  public lastTVDownloadActivityDate(watchShow: any): string {
    // returns the last season/episode download date for a tv show
    const episodes = this.apiService.watchTVEpisodes.filter((episode) => {
      return episode.watch_tv_show === watchShow.id;
    });
    const seasons = this.apiService.watchTVSeasons.filter((season) => {
      return season.watch_tv_show === watchShow.id;
    });
    // sort by collected date desc
    seasons.sort((a, b) => {
      return (a.collected_date > b.collected_date) ? 1 : -1;
    }).reverse();
    episodes.sort((a, b) => {
      return (a.collected_date > b.collected_date) ? 1 : -1;
    }).reverse();

    let last_download_date = '';

    if (episodes.length && episodes[0].collected_date) {
      last_download_date = episodes[0].collected_date;
    }
    if (seasons.length && seasons[0].collected_date) {
      if (last_download_date < seasons[0].collected_date) {
        last_download_date = seasons[0].collected_date;
      }
    }
    return last_download_date;
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }

  protected _buildResults(mediaType: string) {
    // get results and define table columns based on tv/movie type
    if (mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      this.results = this.apiService.watchTVShows;
    } else {
      this.results = this.apiService.watchMovies;
    }
  }
}
