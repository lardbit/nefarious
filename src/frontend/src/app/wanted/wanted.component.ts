import { ChangeDetectorRef } from '@angular/core';
import {Component, OnInit, OnDestroy } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import * as _ from 'lodash';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-wanted',
  templateUrl: './wanted.component.html',
  styleUrls: ['./wanted.component.css']
})
export class WantedComponent implements OnInit, OnDestroy {
  public results: any[] = [];
  public mediaType: string;
  public search = '';

  protected _changes: Subscription;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
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
