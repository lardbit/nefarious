import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-search-tabs',
  templateUrl: './search-tabs.component.html',
  styleUrls: ['./search-tabs.component.css']
})
export class SearchTabsComponent implements OnInit {
  public queryParams: any;

  constructor(
    private route: ActivatedRoute,
  ) { }

  ngOnInit() {
    this.route.queryParams.subscribe(
      (params) => {
        this.queryParams = params;
      }
    )
  }

}
