import { ActivatedRoute, Router } from '@angular/router';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { UntypedFormBuilder, UntypedFormGroup } from '@angular/forms';
import { debounceTime } from 'rxjs/operators';
import { ToastrService } from 'ngx-toastr';


const RESULTS_PER_PAGE = 32;


@Component({
  selector: 'app-rotten-tomatoes',
  templateUrl: './rotten-tomatoes.component.html',
  styleUrls: ['./rotten-tomatoes.component.css']
})
export class RottenTomatoesComponent implements OnInit {
  public results: any[] = [];
  public isLoading = false;
  public form: UntypedFormGroup;
  public sortBy = {
    'Popularity': 'popular',
    'Newest': 'newest',
    'Title': 'a_z',
    'Critic Score': 'critic_highest',
    'Audience Score': 'audience_highest',
  };
  public critics = {
    'Fresh': 'fresh',
    'Certified Fresh': 'certified_fresh',
  };
  public types = {
    'At Home': 'movies_at_home',
    'In Theaters': 'movies_in_theaters',
    'Coming soon': 'movies_coming_soon',
  };

  constructor(
    private apiService: ApiService,
    private fb: UntypedFormBuilder,
    private toastr: ToastrService,
    private route: ActivatedRoute,
    private router: Router,
  ) {
  }

  ngOnInit(): void {

    // build form
    this.form = this.fb.group({
      type: this.route.snapshot.queryParams['type'] || this.types['At Home'],
      critics: this.route.snapshot.queryParams['critics'] || this.critics['Fresh'],
      sortBy: this.route.snapshot.queryParams['sortBy'] || this.sortBy['Popularity'],
      page: parseInt(this.route.snapshot.queryParams['page'], 10) || 1,
    });

    this.route.queryParams.subscribe((params) => {
      this.form.patchValue(params, {emitEvent: false});
      this._search();
    });

    // react to changes
    this.form.valueChanges.pipe(
      debounceTime(250),
    ).subscribe((type) => {
      this._setPage(1);
      this._updateRoute();
      this._search();
    });
  }

  public hasNextPage(): boolean {
    return this.results.length >= RESULTS_PER_PAGE;
  }

  public next() {
    this._setPage(parseInt(this.form.get('page').value, 10) + 1);
    this._updateRoute();
  }

  public previous() {
    if (this.form.get('page').value > 1) {
      this._setPage(parseInt(this.form.get('page').value, 10) - 1);
    }
    this._updateRoute();
  }

  protected _search() {
    this.isLoading = true;

    this.apiService.discoverRottenTomatoesMedia('movie', this.form.value).subscribe(
      (data: any) => {
        this.results = data.results || [];
      },
      (error) => {
        this.toastr.error('An unknown error occurred');
        this.isLoading = false;
      }, () => {
        this.isLoading = false;
      }
    );
  }

  protected _updateRoute() {
    this.router.navigate([], {queryParams: this.form.value});
  }

  protected _setPage(page: number) {
    this.form.get('page').setValue(page, {emitEvent: false});
  }
}
