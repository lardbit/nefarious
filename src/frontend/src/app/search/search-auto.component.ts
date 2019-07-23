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
  public results: any[] = [];
  public isSearching = false;
  public errorMessage: string;
  public type: string;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private route: ActivatedRoute,
    private router: Router,
    ) {
  }

  ngOnInit() {
    // auto search on load if query params exist
    if (this.route.snapshot.queryParams['q'] && this.route.snapshot.queryParams['type']) {
      this.search(this.route.snapshot.queryParams);
    }
  }

  public searchMediaType() {
    return this.type;
  }

  public userIsStaff() {
    return this.apiService.userIsStaff();
  }

  public search(queryParams: any) {
    this.type = queryParams.type;

    // add the search query to the route parameters
    this.router.navigate(
      [],
      {
        relativeTo: this.route,
        queryParams: queryParams,
      },
    );

    this.errorMessage = null;
    this.results = [];
    this.isSearching = true;

    console.log('Searching %s for %s', queryParams.type, queryParams.q);

    let query;

    const similarToMediaQueryRegEx = /^similar-to:(\d+)$/;
    const recommendedToMediaQueryRegEx = /^recommended-to:(\d+)$/;

    // execute "similar to media" query or standard search query
    if (similarToMediaQueryRegEx.test(queryParams['q'])) {
      query = this.apiService.searchSimilarMedia(queryParams['q'].match(similarToMediaQueryRegEx)[1], queryParams.type);
    } else if (recommendedToMediaQueryRegEx.test(queryParams['q'])) {
      query = this.apiService.searchRecommendedMedia(queryParams['q'].match(recommendedToMediaQueryRegEx)[1], queryParams.type);
    } else {
      query = this.apiService.searchMedia(queryParams.q, queryParams.type);
    }

    query.subscribe(
      (data) => {
        // remove results without a poster image
        this.results = data.results.filter((result) => {
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
        if (this.results.length <= 0) {
          this.errorMessage = 'No results';
        }
      }
    );
  }
}
