import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, Validators} from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import * as _ from 'lodash';
import { tap } from 'rxjs/operators';
import { Observable, zip } from 'rxjs';

@Component({
  selector: 'app-discover',
  templateUrl: './discover.component.html',
  styleUrls: ['./discover.component.css']
})
export class DiscoverComponent implements OnInit {
  public results: any[] = [];
  public form;
  public isLoading = true;
  public movieGenres: {
    id: number,
    name: string
  }[];
  public tvGenres: {
    id: number,
    name: string
  }[];

  public DEFAULT_SORT = 'popularity.desc';
  public OPTIONS_SORT = [
    {name: 'Release Date (newest)', value: 'primary_release_date.desc'},
    {name: 'Release Date (oldest)', value: 'primary_release_date.asc'},
    {name: 'Most Popular', value: 'popularity.desc'},
    {name: 'Least Popular', value: 'popularity.asc'},
    {name: 'Highest Votes', value: 'vote_average.desc'},
    {name: 'Lowest Votes', value: 'vote_average.asc'},
    {name: 'Highest Revenue', value: 'revenue.desc'},
    {name: 'Lowest Revenue', value: 'revenue.asc'},
  ];

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
  ) {
  }

  ngOnInit() {

    this.form = this.fb.group({
      'mediaType': [this.apiService.SEARCH_MEDIA_TYPE_MOVIE, Validators.required],
      'sort_by': [this.DEFAULT_SORT, Validators.required],
      'primary_release_date.gte': ['', Validators.pattern('\d{4}')],
      'primary_release_date.lte': ['', Validators.pattern('\d{4}')],
      'with_genres': ['', Validators.pattern('\d+')],
      'page': [1, Validators.pattern('\d+')],
    });

    // auto submit search if there were filters set in the URL
    if (this.route.snapshot.params) {
      // set the url param values on the form
      _.forOwn(this.route.snapshot.params, (value, key) => {
        if (value) {
          this.form.controls[key].setValue(value);
        }
      });
      this.search();
    }

    this._fetchGenres().subscribe(
      () => {
        this.isLoading = false;
      },
      (error) => {
        console.error(error);
        this.toastr.error('An error occurred fetching genres');
        this.isLoading = false;
      }
    );
  }

  public search(appendResults: boolean = false) {
    this.isLoading = true;

    if (!appendResults) {
      this.results = [];
      // reset the page value
      this.form.controls['page'].setValue(1);
    }

    const currentUrl = this.route.snapshot.url.map((data) => {
      return data.path;
    });

    const discoverEndpoint = this.form.value.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE ?
      this.apiService.discoverMovies(this._formValues()) :
      this.apiService.discoverTV(this._formValues());

    // update the url params then search
    this.router.navigate([`/${currentUrl.join('/')}/`, this._formValues()]).then(
      () => {
        discoverEndpoint.subscribe(
          (data: any) => {
            this.results = this.results.concat(data.results);
            // increment the "page" input value
            this.form.controls['page'].setValue(data.page + 1);
            this.isLoading = false;
          },
          (error) => {
            this.toastr.error('An unknown error occurred');
            this.isLoading = false;
          }
        );
      }
    );
  }

  protected _fetchGenres(): Observable<any> {
    this.tvGenres = [];
    this.movieGenres = [];

    return zip(
      this.apiService.fetchMovieGenres().pipe(
        tap((data: any) => {
          this.movieGenres = data.genres;
        })
      ),
      this.apiService.fetchTVGenres().pipe(
        tap((data: any) => {
          this.tvGenres = data.genres;
        })
      ),
    );
  }

  protected _formValues() {
    // returns populated values
    const values = {};
    _.forOwn(this.form.value, (value, key) => {
      if (value) {
        values[key] = value;
      }
    });
    return values;
  }
}
