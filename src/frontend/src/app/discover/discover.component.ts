import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, Validators} from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import * as _ from 'lodash';
import { tap } from 'rxjs/operators';
import { Observable, zip } from 'rxjs';
import * as moment from 'moment';


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

    this.route.params.subscribe(
      (params) => {
        this.form = this._initialForm();
        // set the url param values on the form
        _.forOwn(params, (value, key) => {
          if (value) {
            this.form.controls[key].setValue(value);
          }
        });
        this._search();
      });

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

  public search(paginate: boolean = false) {

    // conditionally increment the "page" input value
    if (paginate) {
      this.form.controls['page'].setValue(parseInt(this.form.get('page').value, 10) + 1);
    }

    const currentUrl = this.route.snapshot.url.map((data) => {
      return data.path;
    });

    // update the url params
    this.router.navigate([`/${currentUrl.join('/')}/`, this._formValues()]);
  }

  protected _search() {
    this.isLoading = true;

    const params = this._formValues();

    // update "greater than" release year to be a full date on beginning of year, i.e 2020-01-01
    if (params['primary_release_date.gte']) {
      params['primary_release_date.gte'] = moment(params['primary_release_date.gte'], 'YYYY').month(0).date(1).format('YYYY-MM-DD');
    }
    // update "less than" release year to be a full date on end of year, i.e 2020-12-31
    if (params['primary_release_date.lte']) {
      params['primary_release_date.lte'] = moment(params['primary_release_date.lte'], 'YYYY').month(11).date(31).format('YYYY-MM-DD');
    }

    let discoverEndpoint;
    if (this.form.value.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE) {
      discoverEndpoint = this.apiService.discoverMovies(params);
    } else {
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
      'primary_release_date.gte': ['', Validators.pattern('\d{4}')],
      'primary_release_date.lte': ['', Validators.pattern('\d{4}')],
      'with_genres': ['', Validators.pattern('\d+')],
      'page': [1, Validators.pattern('\d+')],
    });
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
