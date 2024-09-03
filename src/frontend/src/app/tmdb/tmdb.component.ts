import { Component, OnInit, ViewChild } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { UntypedFormBuilder, Validators} from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { tap } from 'rxjs/operators';
import {forkJoin, Observable, zip} from 'rxjs';
import * as moment from 'moment';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';


@Component({
  selector: 'app-tmdb',
  templateUrl: './tmdb.component.html',
  styleUrls: ['./tmdb.component.css']
})
export class TmdbComponent implements OnInit {
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
  public regions: {
    iso_3166_1: string,
    native_name: string
  }[];
  @ViewChild('nav', {static: true}) navEl: NgbNav;

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
    private fb: UntypedFormBuilder,
    private route: ActivatedRoute,
    private router: Router,
  ) {
  }

  ngOnInit() {

    this.route.queryParams.subscribe(
      (params) => {
        this.form = this._initialForm();
        // set the url param values on the form
        Object.keys(params).forEach((key) => {
          if (params[key]) {
            this.form.controls[key].setValue(params[key]);
          }
        });
        this._search();
      });

    // fetch tmdb filterable data
    forkJoin([
      this._fetchGenres(),
      this.apiService.fetchRegions().pipe(
        tap((data) => this.regions = data.results),
      ),
    ])
    .subscribe(
      {
        error: (error) => {
          console.error(error);
          this.toastr.error('An error occurred fetching filter data');
        }
      }
    )
  }

  public search(paginate: boolean = false) {

    // conditionally increment the "page" input value
    if (paginate) {
      this.form.controls['page'].setValue(parseInt(this.form.get('page').value, 10) + 1);
    }

    // update the url params
    this.router.navigate([], {queryParams: this._formValues()});
  }

  protected _search() {
    this.isLoading = true;

    const params = this._formValues();

    // update "greater than" release year to be a full date on beginning of year, i.e. 2020-01-01
    // and include proper key name with `.gte`
    if (params['primary_release_date_gte']) {
      params['primary_release_date.gte'] = moment(params['primary_release_date_gte'], 'YYYY').month(0).date(1).format('YYYY-MM-DD');
      delete params['primary_release_date_gte'];
    }
    // update "less than" release year to be a full date on end of year, i.e. 2020-12-31
    // and include proper key name with `.lte`
    if (params['primary_release_date_lte']) {
      params['primary_release_date.lte'] = moment(params['primary_release_date_lte'], 'YYYY').month(11).date(31).format('YYYY-MM-DD');
      delete params['primary_release_date_lte'];
    }

    let discoverEndpoint;
    if (this.form.value.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE) {
      discoverEndpoint = this.apiService.discoverMovies(params);
    } else { // tv
      // update the "release date" parameter to "air_date"
      if (params['primary_release_date.gte']) {
        params['air_date.gte'] = params['primary_release_date.gte'];
        delete params['primary_release_date.gte'];
      }
      if (params['primary_release_date.lte']) {
        params['air_date.lte'] = params['primary_release_date.lte'];
        delete params['primary_release_date.lte'];
      }
      discoverEndpoint = this.apiService.discoverTV(params);
    }

    discoverEndpoint.subscribe(
      (data: any) => {
        this.results = data.results;
        this.isLoading = false;
      },
      (error) => {
        this.toastr.error('An unknown error occurred');
        this.isLoading = false;
      }
    );

  }

  protected _initialForm() {
    return this.fb.group({
      'mediaType': [this.apiService.SEARCH_MEDIA_TYPE_MOVIE, Validators.required],
      'sort_by': [this.DEFAULT_SORT, Validators.required],
      // FormGroup keys cannot include `.`, so we'll replace them later (e.g. primary_release_date.gte, primary_release_date.lte)
      'primary_release_date_gte': ['', Validators.pattern('\d{4}')],
      'primary_release_date_lte': ['', Validators.pattern('\d{4}')],
      'with_genres': ['', Validators.pattern('\d+')],
      'region': ['', Validators.pattern('\w{2}')], // iso_3166_1 (2 character region code)
      'page': [1, Validators.pattern('\d+')],
    });
  }

  protected _fetchGenres(): Observable<any> {
    this.tvGenres = [];
    this.movieGenres = [];

    return forkJoin([
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
    ]);
  }

  protected _formValues() {
    // returns populated values
    const values = {};
    Object.keys(this.form.value).forEach((key) => {
      if (this.form.value[key]) {
        values[key] = this.form.value[key];
      }
    });
    return values;
  }
}
