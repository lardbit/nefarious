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
        if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
          this.results = this.apiService.watchTVShows;
        } else {
          this.results = this.apiService.watchMovies;
        }
      }
    );
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }
}
