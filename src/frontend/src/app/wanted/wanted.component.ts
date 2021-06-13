import { NgZone } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import * as _ from 'lodash';
import { Subscription } from 'rxjs';
import { ColumnMode } from '@swimlane/ngx-datatable';
import { DatePipe } from '@angular/common';
import { MediaFilterPipe } from '../filter.pipe';

@Component({
  selector: 'app-wanted',
  templateUrl: './wanted.component.html',
  styleUrls: ['./wanted.component.css'],
  providers: [DatePipe],
})
export class WantedComponent implements OnInit, OnDestroy {
  public results: any[] = [];
  public mediaType: string;
  public search = '';
  public ColumnMode = ColumnMode;

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

    this.results = _.filter(wanted, (watchMedia) => {
      return !watchMedia.collected;
    });

  }

}
