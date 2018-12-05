import { Component, OnInit } from '@angular/core';
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
  ) {
  }

  ngOnInit() {
    this.form = this.fb.group({
      'sort_by': [this.DEFAULT_SORT, Validators.required],
      'release_date_gte': ['', Validators.pattern('\d{4}')],
      'release_date_lte': ['', Validators.pattern('\d{4}')],
    });
  }

  public submit() {
    this.apiService.discoverMovies(this.form.value).subscribe(
      (data: any) => {
        this.results = data.results;
      },
      (error) => {
        this.toastr.error('An unknown error occured');
      }
    )
  }

}
