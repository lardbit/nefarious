import { NgZone } from '@angular/core';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
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
  public qualityProfile: number;
  public isLoading = true;
  public isSaving = false;
  public trailerUrls$: Observable<any>;
  public activeNav = 'details';

  protected _changes: Subscription;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private toastr: ToastrService,
    private ngZone: NgZone,
  ) {
  }

  ngOnInit() {

    const routeParams = this.route.snapshot.params;
    this.apiService.searchMediaDetail(this.apiService.SEARCH_MEDIA_TYPE_MOVIE, routeParams.id).subscribe(
      (data) => {
        this.result = data;
        this.isLoading = false;
        this.watchMovie = this.getWatchMovie();
        this.qualityProfile = this.watchMovie ?
          this.watchMovie.quality_profile :
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
        const trailerVideos = data.results.filter((video) => {
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
        this.ngZone.run(() => {
          this.watchMovie = this.getWatchMovie();
        });
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
        this.result.id, this.result.title, this.mediaPosterURL(this.result), this.result.release_date, this.qualityProfile);
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

  public qualityProfiles(): any[] {
    return this.apiService.qualityProfiles;
  }

  public getWatchMovie() {
    return this.apiService.watchMovies.find((watchMovie) => {
      return this.result && watchMovie.tmdb_movie_id === this.result.id;
    });
  }

  public canUnWatch() {
    return this.userIsStaff() || this.watchMovie.requested_by === this.apiService.user.username;
  }

  public manuallyDownloaded() {
    // update the nav back to the main details
    this.activeNav = 'details';
  }

  public trackByProfile(index: number, item: any) {
    return item.id;
  }
}
