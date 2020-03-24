import { ChangeDetectorRef } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import * as _ from 'lodash';
import {Observable, Subscription} from 'rxjs';
import { map, share } from 'rxjs/operators';


@Component({
  selector: 'app-media-movie',
  templateUrl: './media-movie.component.html',
  styleUrls: ['./media-movie.component.css']
})
export class MediaMovieComponent implements OnInit, OnDestroy {
  public result: any;
  public watchMovie: any;
  public qualityProfileCustom: string;
  public isLoading = true;
  public isSaving = false;
  public trailerUrls$: Observable<any>;

  protected _changes: Subscription;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private toastr: ToastrService,
    private changeDetectorRef: ChangeDetectorRef
  ) {
  }

  ngOnInit() {

    const routeParams = this.route.snapshot.params;
    this.apiService.searchMediaDetail(this.apiService.SEARCH_MEDIA_TYPE_MOVIE, routeParams.id).subscribe(
      (data) => {
        this.result = data;
        this.isLoading = false;
        this.watchMovie = this.getWatchMovie();
        this.qualityProfileCustom = this.watchMovie ?
          this.watchMovie.quality_profile_custom :
          this.apiService.settings.quality_profile_movies;
      },
      (error) => {
        this.isLoading = false;
        this.toastr.error('An unknown error occurred');
      }
    );

    // fetch trailers
    this.trailerUrls$ = this.apiService.fetchMediaVideos(this.apiService.SEARCH_MEDIA_TYPE_MOVIE, routeParams.id).pipe(
      share(),
      map((data) => {
        const trailerVideos = _.filter(data.results, (video) => {
          return video.type === 'Trailer' && video.site === 'YouTube';
        });
        return trailerVideos.map((video) => {
          return `https://www.youtube.com/watch?v=${video.key}`;
        });
      })
    );

    // watch for updated media
    this._changes = this.apiService.mediaUpdated$.subscribe(
      () => {
        this.watchMovie = this.getWatchMovie();
        this.changeDetectorRef.detectChanges();
      }
    );
  }

  ngOnDestroy() {
    this._changes.unsubscribe();
  }

  public isWatchingMovie() {
    return !!this.getWatchMovie();
  }

  public submit() {
    this.isSaving = true;
    const watchMovie = this.getWatchMovie();
    const isWatchingMovie = !this.isWatchingMovie();  // toggle to new requested state

    let endpoint;

    if (isWatchingMovie) {
      endpoint = this.apiService.watchMovie(
        this.result.id, this.result.title, this.mediaPosterURL(this.result), this.result.release_date, this.qualityProfileCustom);
    } else if (!isWatchingMovie && watchMovie) {
      endpoint = this.apiService.unWatchMovie(watchMovie.id);
    } else {
      return;
    }

    endpoint.subscribe(
      (data) => {
        let verb;
        if (isWatchingMovie) {
          this.watchMovie = data;
          verb = 'Watching';
        } else {
          verb = 'Stop watching';
          this.watchMovie = null;
        }
        const message = `${verb} ${this.result.title}`;
        this.toastr.success(message);
        this.isSaving = false;
      },
      (error) => {
        console.error(error);
        this.toastr.error('An unknown error occurred');
        this.isSaving = false;
      }
    );
  }

  public mediaPosterURL(result) {
    return `${this.apiService.settings.tmdb_configuration.images.secure_base_url}/original/${result.poster_path}`;
  }

  public userIsStaff(): boolean {
    return this.apiService.userIsStaff();
  }

  public qualityProfiles(): string[] {
    return this.apiService.qualityProfiles;
  }

  public getWatchMovie() {
    return _.find(this.apiService.watchMovies, (watchMovie) => {
      return watchMovie.tmdb_movie_id === this.result.id;
    });
  }

  public canUnWatch() {
    return this.userIsStaff() || this.watchMovie.requested_by === this.apiService.user.username;
  }
}
