import { Component, OnInit } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-search-auto',
  templateUrl: './search-auto.component.html',
  styleUrls: ['./search-auto.component.css']
})
export class SearchAutoComponent implements OnInit {
  public results: any[] = [];
  public isSearching = false;
  public errorMessage: string;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    ) {
  }

  ngOnInit() {
  }

  public searchMediaType() {
    return this.apiService.searchQuery.type;
  }

  public isSearchingTV() {
    return this.apiService.searchQuery.type === this.apiService.SEARCH_MEDIA_TYPE_TV;
  }

  public isSearchingMovies() {
    return this.apiService.searchQuery.type === this.apiService.SEARCH_MEDIA_TYPE_MOVIE;
  }

  public mediaPosterURL(result) {
    return `${this.apiService.settings.tmdb_configuration.images.base_url}/original/${result.poster_path}`;
  }

  public search() {
    this.errorMessage = null;
    this.results = [];
    this.isSearching = true;

    console.log('Searching %s for %s', this.apiService.searchQuery.type, this.apiService.searchQuery.query);

    this.apiService.searchMedia(this.apiService.searchQuery.query, this.apiService.searchQuery.type).subscribe(
      (data) => {
        console.log(data);
        this.results = data.results.filter((result) => {
          return result.poster_path;
        });
        this.isSearching = false;
      },
      (error) => {
        this.isSearching = false;
        this.toastr.error('An unknown error occurred');
        console.log(error);
      },
      () => {
        if (this.results.length <= 0) {
          this.errorMessage = 'No results';
        }
      }
    );
  }

}
