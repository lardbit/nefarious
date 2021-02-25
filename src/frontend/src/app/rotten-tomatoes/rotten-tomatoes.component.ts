import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { FormBuilder, FormGroup } from '@angular/forms';
import { debounceTime } from 'rxjs/operators';
import { ToastrService } from 'ngx-toastr';


@Component({
  selector: 'app-rotten-tomatoes',
  templateUrl: './rotten-tomatoes.component.html',
  styleUrls: ['./rotten-tomatoes.component.css']
})
export class RottenTomatoesComponent implements OnInit {
  public results: any[] = [];
  public isLoading = false;
  public form: FormGroup;
  public sortBy = {
    'Release': 'release',
    'Score': 'tomato',
    'Popularity': 'popularity',
  };
  public types = {
    'Opening': 'opening',
    'Upcoming': 'upcoming',
    'In Theaters': 'in-theaters',
    'In Theaters (Certified Fresh)': 'cf-in-theaters',
    'DVD All': 'dvd-streaming-all',
    'Top DVD': 'top-dvd-streaming',
    'DVD New': 'dvd-streaming-new',
    'DVD Upcoming': 'dvd-streaming-upcoming',
    'DVD All (Certified Fresh)': 'cf-dvd-streaming-all',
  };

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private toastr: ToastrService,
  ) {
  }

  ngOnInit(): void {

    // build form
    this.form = this.fb.group({
      type: this.types['In Theaters'],
      sortBy: this.sortBy['Popularity'],
      page: 1,
      minTomato: 70,
    });

    // react to changes
    this.form.valueChanges.pipe(
      debounceTime(250),
    ).subscribe((type) => {
      this._search();
    });

    this._search();
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
}
