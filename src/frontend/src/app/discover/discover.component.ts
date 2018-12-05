import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, Validators} from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-discover',
  templateUrl: './discover.component.html',
  styleUrls: ['./discover.component.css']
})
export class DiscoverComponent implements OnInit {
  public results: any[];
  public form;
  public isSearching = false;

  public DEFAULT_SORT = 'popularity.desc';
  public OPTIONS_SORT = [
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
      'sort_by': [this.DEFAULT_SORT, Validators.required],
      'primary_release_date.gte': ['', Validators.pattern('\d{4}')],
      'primary_release_date.lte': ['', Validators.pattern('\d{4}')],
    });

    // auto submit search if there were filters already set in the URL
    if (this.route.snapshot.params) {
      this.form.setValue(this.route.snapshot.params);
      this.search();
    }
  }

  public search() {
    this.isSearching = true;
    this.results = [];

    let currentUrl = this.route.snapshot.url.map((data) => {
      return data.path;
    });

    // navigate to the search component with the search query as parameters
    this.router.navigate([`/${currentUrl.join('/')}/`, this.form.value]).then(
      () => {
        this.apiService.discoverMovies(this.form.value).subscribe(
          (data: any) => {
            this.results = data.results;
            this.isSearching = false;
          },
          (error) => {
            this.toastr.error('An unknown error occured');
            this.isSearching = false;
          }
        );
      }
    );
  }

}
