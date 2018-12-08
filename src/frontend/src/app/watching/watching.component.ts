import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';


@Component({
  selector: 'app-watching',
  templateUrl: './watching.component.html',
  styleUrls: ['./watching.component.css']
})
export class WatchingComponent implements OnInit {
  public results: any[];
  public alertMessage: string;
  public mediaType: string;

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {
    this.route.params.subscribe(
      (params) => {
        this.alertMessage = null;
        this.mediaType = params.type;
        if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
          this.results = this.apiService.watchTVShows;
        } else {
          this.results = this.apiService.watchMovies;
        }

        if (this.results.length <= 0) {
          this.alertMessage = 'You are not watching anything yet';
        }
      }
    );
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }
}
