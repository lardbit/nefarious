import { Component, OnInit, Input } from '@angular/core';
import { ApiService } from '../api.service';
import * as _ from 'lodash';

@Component({
  selector: 'app-media-results',
  templateUrl: './media-results.component.html',
  styleUrls: ['./media-results.component.css']
})
export class MediaResultsComponent implements OnInit {
  @Input() results: any[];
  @Input() mediaType: string;
  public search = '';

  constructor(
    private apiService: ApiService,
  ) {
  }

  ngOnInit() {
  }

  public isWatchingResult(result: any): boolean {
    if (this.isSearchingTV()) {
      const watchingEpisode = _.find(this.apiService.watchTVEpisodes, (watch) => {
        return watch.tmdb_show_id === result.id;
      });
      const watchingSeason = _.find(this.apiService.watchTVSeasons, (watch) => {
        return watch.tmdb_show_id === result.id;
      });
      return watchingEpisode || watchingSeason;
    } else {
      return _.find(this.apiService.watchMovies, (watch) => {
        return watch.tmdb_movie_id === result.id;
      });
    }
  }

  public isSearchingTV() {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV;
  }

  public isSearchingMovies() {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE;
  }

  public mediaPosterURL(result) {
    return `${this.apiService.settings.tmdb_configuration.images.base_url}/original/${result.poster_path}`;
  }
}
