import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import * as _ from 'lodash';


@Component({
  selector: 'app-search-auto-media-movie',
  templateUrl: './media-movie.component.html',
  styleUrls: ['./media-movie.component.css']
})
export class MediaMovieComponent implements OnInit {
  public result: any;
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
        this.isWatchingMovie = !!this.getWatchMovie();
      },
      (error) => {
        this.isLoading = false;
        this.toastr.error('An unknown error occurred');
      }
    );
  }

  public submit() {
    let endpoint;
    const watchMovie = this.getWatchMovie();

    if (this.isWatchingMovie && !watchMovie) {
      endpoint = this.apiService.watchMovie(this.result.id, this.result.original_title, this.mediaPosterURL(this.result));
    } else if (!this.isWatchingMovie && watchMovie ) {
      endpoint = this.apiService.unWatchMovie(watchMovie.id);
    } else {
      return;
    }

    endpoint.subscribe(
      () => {
        let verb;
        if (this.isWatchingMovie) {
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

  public hasWatchMovieTransmissionId() {
    const watchMovie = this.getWatchMovie();
    return watchMovie && watchMovie.transmission_torrent_id;
  }
}
