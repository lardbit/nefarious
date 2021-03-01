import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';
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
  public isLoading = false;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private toastr: ToastrService,
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

  public navigateToMedia(result: any) {
    // rotten tomato results must be searched against tmdb and then routed
    if (this.isRottenTomatoResult(result)) {
      this.isLoading = true;
      this.apiService.searchMedia(result.title, this.mediaType).subscribe(
        (data) => {
          if (data.results && data.results.length > 0) {
            // try and find an exact match, otherwise fallback to first result
            let match = data.results.find((movie) => {
              return movie.title === result.title;
            });
            if (!match) {
              match = data.results[0];
            }
            this.router.navigate(['/media', this.mediaType, match.id]);
          } else {
            this.toastr.error('No results found for title in TMDB');
          }
        },
        (error) => {
          console.error(error);
          this.toastr.error('An unknown error occurred');
          this.isLoading = false;
        },
        () => {
          this.isLoading = false;
        },
      );
    } else {
      this.router.navigate(['/media', this.mediaType, result.id]);
    }
  }

  public isRottenTomatoResult(result): boolean {
    return result.provider === 'rotten-tomatoes';
  }

  protected _watchingResult(result: any) {

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
}
