import { ActivatedRoute } from '@angular/router';
import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-search-input',
  templateUrl: './search-input.component.html',
  styleUrls: ['./search-input.component.css']
})
export class SearchInputComponent implements OnInit {
  @Output() query = new EventEmitter<any>();
  public q: string;
  public type: string;

  constructor(
    private toastr: ToastrService,
    private apiService: ApiService,
    private route: ActivatedRoute,
    ) {
  }

  ngOnInit() {
    this.type = this.apiService.SEARCH_MEDIA_TYPE_MOVIE;

    const queryParams = this.route.snapshot.queryParams;

    // populate query params if already set
    if (queryParams['q'] && queryParams['type']) {
      this.type = queryParams['type'];
      this.q = queryParams['q'];
    }
  }

  public submitSearch() {
    this.query.emit({q: this.q, type: this.type});
  }
}
