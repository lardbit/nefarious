import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import * as _ from 'lodash';


@Component({
  selector: 'app-media-movie',
  templateUrl: './media-movie.component.html',
  styleUrls: ['./media-movie.component.css']
})
export class MediaMovieComponent implements OnInit {
  public result: any;
  public watchMovie: any;
  public qualityProfileCustom: string;
  public isLoading = true;
  public isSaving = false;
  public isWatchingMovie = false;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private toastr: ToastrService,
  ) {
  }

  ngOnInit() {
    const routeParams = this.route.snapshot.params;
    this.apiService.searchMediaDetail(this.apiService.SEARCH_MEDIA_TYPE_MOVIE, routeParams.id).subscribe(
      (data) => {
        this.result = data;
        this.isLoading = false;
        this.watchMovie = this.getWatchMovie();
        this.isWatchingMovie = !!this.watchMovie;
        this.qualityProfileCustom = this.watchMovie ? this.watchMovie.quality_profile_custom : '';
      },
      (error) => {
        this.isLoading = false;
        this.toastr.error('An unknown error occurred');
      }
    );
  }

  public submit() {
    let endpoint;

    if (this.isWatchingMovie) {
      endpoint = this.apiService.watchMovie(this.result.id, this.result.original_title, this.mediaPosterURL(this.result), this.qualityProfileCustom);
    } else if (!this.isWatchingMovie && this.watchMovie) {
      endpoint = this.apiService.unWatchMovie(this.watchMovie.id);
    } else {
      return;
    }

    endpoint.subscribe(
      (data) => {
        let verb;
        if (this.isWatchingMovie) {
          this.watchMovie = data;
          verb = 'Watching';
        } else {
          verb = 'Stop watching';
        }
        this.toastr.success(`${verb} ${this.result.original_title}`);
      },
      (error) => {
        console.log(error);
        this.toastr.error('An unknown error occurred');
      }
    );
  }

  public mediaPosterURL(result) {
    return `${this.apiService.settings.tmdb_configuration.images.base_url}/original/${result.poster_path}`;
  }

  public getWatchMovie() {
    return _.find(this.apiService.watchMovies, (watchMovie) => {
      return watchMovie.tmdb_movie_id === this.result.id;
    });
  }

  public userIsStaff(): boolean {
    return this.apiService.userIsStaff();
  }

  public qualityProfiles(): string[] {
    return this.apiService.qualityProfiles;
  }
}
