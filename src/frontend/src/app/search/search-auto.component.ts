import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-search-auto',
  templateUrl: './search-auto.component.html',
  styleUrls: ['./search-auto.component.css']
})
export class SearchAutoComponent implements OnInit {
  public page = 1;
  public searchResults: {
    page: number,
    results: any[],
    total_pages: number,
  } = {
    page: 0,
    results: [],
    total_pages: 0,
  };
  public isSearching = false;
  public errorMessage: string;
  public type: string;
  public q = '';

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private route: ActivatedRoute,
    private router: Router,
    ) {
  }

  ngOnInit() {
    // search when query params change
    this.route.queryParams.subscribe((params) => {
      if (params['q'] && params['type']) {
        this.search(params);
      }
    });
  }

  public searchMediaType() {
    return this.type;
  }

  public userIsStaff() {
    return this.apiService.userIsStaff();
  }

  public search(queryParams: any) {

    this.type = queryParams.type;
    this.q = queryParams.q;
    this.page = parseInt(queryParams.page || 1, 10);

    // add the search query to the route parameters
    this.router.navigate(
      [],
      {
        relativeTo: this.route,
        queryParams: queryParams,
      },
    );

    this.errorMessage = null;
    this.searchResults.results = [];
    this.isSearching = true;

    console.log('Searching %s for "%s"', queryParams.type, queryParams.q);

    let query;

    const similarToMediaQueryRegEx = /^similar-to:(\d+)$/;
    const recommendedToMediaQueryRegEx = /^recommended-to:(\d+)$/;

    // execute "similar to media" query or standard search query
    if (similarToMediaQueryRegEx.test(queryParams['q'])) {
      query = this.apiService.searchSimilarMedia(queryParams['q'].match(similarToMediaQueryRegEx)[1], queryParams.type);
    } else if (recommendedToMediaQueryRegEx.test(queryParams['q'])) {
      query = this.apiService.searchRecommendedMedia(queryParams['q'].match(recommendedToMediaQueryRegEx)[1], queryParams.type);
    } else {
      query = this.apiService.searchMedia(queryParams.q, queryParams.type, this.page);
    }

    query.subscribe(
      (data) => {
        this.searchResults = data;
        // remove results without a poster image
        this.searchResults.results = data.results.filter((result) => {
          return result.poster_path;
        });
        this.isSearching = false;
      },
      (error) => {
        this.isSearching = false;
        this.toastr.error('An unknown error occurred');
        console.error(error);
      },
      () => {
        if (this.searchResults.results.length <= 0) {
          this.errorMessage = 'No results';
        }
      }
    );
  }

  public nextPage(pageForward: number) {
    this.page += pageForward;
    this.search({type: this.type, q: this.q, page: this.page});
  }
}
