import { NgZone } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { Subscription } from 'rxjs';
import { MediaFilterPipe } from '../filter.pipe';


@Component({
  selector: 'app-watching',
  templateUrl: './watching.component.html',
  styleUrls: ['./watching.component.css']
})
export class WatchingComponent implements OnInit, OnDestroy {
  public results: any[] = [];
  public mediaType: string;
  public search: string;
  public page = 0;
  public pageSize = 100;

  protected _changes: Subscription;

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private mediaFilter: MediaFilterPipe,
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
    // return all results filtered by search query
    if (this.search) {
      return this.mediaFilter.transform(this.results, this.search);
    }
    // return paginated results
    return this.results
      .map((result, i) => ({id: i + 1, ...result}))
      .slice((this.page - 1) * this.pageSize, (this.page - 1) * this.pageSize + this.pageSize);
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }

  protected _buildResults(mediaType: string) {
    if (mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      this.results = this.apiService.watchTVShows;
    } else {
      this.results = this.apiService.watchMovies;
    }
  }
}
