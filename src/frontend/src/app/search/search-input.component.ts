import { ActivatedRoute, Router } from '@angular/router';
import { Component, EventEmitter, OnInit, Output, Input } from '@angular/core';
import { ApiService } from "../api.service";
import { ToastrService } from "ngx-toastr";

@Component({
  selector: 'app-search-input',
  templateUrl: './search-input.component.html',
  styleUrls: ['./search-input.component.css']
})
export class SearchInputComponent implements OnInit {
  @Output() query = new EventEmitter<any>();
  @Input() isSearching: boolean;

  public searchQuery: {
    query: string,
    type: string,
  };

  constructor(
    private toastr: ToastrService,
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router,
    ) {
  }

  ngOnInit() {
    // link component instance value to service value
    this.searchQuery = this.apiService.searchQuery;

    // see if there were router params already set
    if (this.route.snapshot.params['q'] && this.route.snapshot.params['type']) {
      this.apiService.searchQuery.query = this.route.snapshot.params['q'];
      this.apiService.searchQuery.type = this.route.snapshot.params['type'];
      this.submitSearch();
    }
  }

  public submitSearch() {
    let currentUrl = this.route.snapshot.url.map((data) => {
      return data.path;
    });
    // navigate to the search component with the search query as parameters
    this.router.navigate([`/${currentUrl.join('/')}/`, {q: this.searchQuery.query, type: this.searchQuery.type}]).then(
      () => {
        // communicate a query was submitted
        this.query.emit();
      },
      () => {
        this.toastr.error('An unknown error occurred');
      }
    );
  }
}
