import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { FormBuilder, FormGroup } from '@angular/forms';

@Component({
  selector: 'app-rotten-tomatoes',
  templateUrl: './rotten-tomatoes.component.html',
  styleUrls: ['./rotten-tomatoes.component.css']
})
export class RottenTomatoesComponent implements OnInit {
  public results: any[] = [];
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
  ) {
  }

  ngOnInit(): void {

    // build form
    this.form = this.fb.group({
      type: this.types['Opening'],
      sortBy: this.sortBy['Release'],
      page: 1,
    });

    // react to changes
    this.form.valueChanges.subscribe((type) => {
      this._search();
    });

    this._search();
  }

  protected _search() {
    this.apiService.discoverRottenTomatoesMedia('movie', this.form.value).subscribe(
      (data: any) => {
        this.results = data.results || [];
      }
    );

  }
}
