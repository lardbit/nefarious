import {Component, OnInit } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import * as _ from 'lodash';

@Component({
  selector: 'app-wanted',
  templateUrl: './wanted.component.html',
  styleUrls: ['./wanted.component.css']
})
export class WantedComponent implements OnInit {
  public results: any[] = [];
  public mediaType: string;
  public search = '';

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {

    // watch for updated media
    this.apiService.mediaUpdated$.subscribe(
      () => {
        this._buildResults(this.mediaType);
      }
    );

    this.route.params.subscribe(
      (params) => {
        this._buildResults(params.type);
      }
    );
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
