import { ChangeDetectorRef } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { Subscription } from 'rxjs';


@Component({
  selector: 'app-watching',
  templateUrl: './watching.component.html',
  styleUrls: ['./watching.component.css']
})
export class WatchingComponent implements OnInit, OnDestroy {
  public results: any[];
  public mediaType: string;
  public search: string;

  protected _changes: Subscription;

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private changeDetectorRef: ChangeDetectorRef
  ) {}

  ngOnInit() {

    // watch for updated media
    this._changes = this.apiService.mediaUpdated$.subscribe(
      () => {
        this._buildResults(this.mediaType);
        this.changeDetectorRef.detectChanges();
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
