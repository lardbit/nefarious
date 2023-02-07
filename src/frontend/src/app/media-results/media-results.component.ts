import { Component, OnInit, Input } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-media-results',
  templateUrl: './media-results.component.html',
  styleUrls: ['./media-results.component.css']
})
export class MediaResultsComponent implements OnInit {
  @Input() results: any[];
  @Input() mediaType: string;
  public search = '';
  public isLoading = false;

  constructor(
    private apiService: ApiService,
  ) {
  }

  ngOnInit() {
  }

  public hasDownloadedResult(result: any): boolean {
    const watchingResult = this._watchingResult(result);
    return watchingResult ? watchingResult.collected : null;
  }

  public isWatchingResult(result: any): boolean {
    return Boolean(this._watchingResult(result));
  }

  public isSearchingTV() {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV;
  }

  public isSearchingMovies() {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE;
  }

  public mediaPosterURL(result) {
    if (this.isRottenTomatoResult(result)) {
      return result.poster_path;
    } else {
      return `${this.apiService.settings.tmdb_configuration.images.secure_base_url}/original/${result.poster_path}`;
    }
  }

  public getMediaURL(result: any) {
    // rotten tomato results must be searched against tmdb first, so we'll redirect to its own component for that
    if (this.isRottenTomatoResult(result)) {
      return ['/rt-redirect', this.mediaType, result.title];
    } else {
      return ['/media', this.mediaType, result.id];
    }
  }

  public isRottenTomatoResult(result): boolean {
    return result.provider === 'rotten-tomatoes';
  }

  protected _watchingResult(result: any) {

    if (this.isSearchingTV()) {
      const watchingEpisode = this.apiService.watchTVEpisodes.find((watch) => {
        return watch.tmdb_show_id === result.id;
      });
      const watchingSeason = this.apiService.watchTVSeasons.find((watch) => {
        return watch.tmdb_show_id === result.id;
      });
      return watchingEpisode || watchingSeason;
    } else {
      return this.apiService.watchMovies.find((watch) => {
        return watch.tmdb_movie_id === result.id;
      });
    }
  }
}
