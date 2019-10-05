import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import * as _ from 'lodash';


@Component({
  selector: 'app-watching',
  templateUrl: './watching.component.html',
  styleUrls: ['./watching.component.css']
})
export class WatchingComponent implements OnInit {
  public results: any[];
  public mediaType: string;
  public search: string;

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {
    this.route.params.subscribe(
      (params) => {
        this.mediaType = params.type;
        let watches: any[];
        if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
          watches = this.apiService.watchTVShows;
        } else {
          watches = this.apiService.watchMovies;
        }

        // filter collected media
        this.results = _.filter(watches, (watchMedia) => {
          return watchMedia.collected;
        });
      }
    );
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }
}
