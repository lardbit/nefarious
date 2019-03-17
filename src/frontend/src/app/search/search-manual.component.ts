import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from "../api.service";
import { ToastrService } from 'ngx-toastr';
import * as _ from 'lodash';


@Component({
  selector: 'app-search',
  templateUrl: './search-manual.component.html',
  styleUrls: ['./search-manual.component.css']
})
export class SearchManualComponent implements OnInit {
  public orderByOptions = ['Name', 'Seeders', 'Size'];
  public results: any[] = [];
  public isSearching: boolean = false;
  public filters: {
    orderBy: string,
  } = {
    orderBy: "Name",
  };
  public type: string;
  protected _downloading: any = {};

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private toastr: ToastrService,
    private router: Router,
    ) {
  }

  ngOnInit() {
    // auto search on load if query params exist
    if (this.route.snapshot.queryParams['q'] && this.route.snapshot.queryParams['type']) {
      this.searchTorrents(this.route.snapshot.queryParams);
    }
  }

  public searchTorrents(queryParams: any) {
    this.type = queryParams.type;

    // add the search query to the route parameters
    this.router.navigate(
      [],
      {
        relativeTo: this.route,
        queryParams: queryParams,
      },
    );

    this.results = [];
    this.isSearching = true;
    this.apiService.searchTorrents(queryParams.q, queryParams.type).subscribe(
      (results) => {
        this.results = results;
        this.filterChange();
        this.isSearching = false;
      }, (error) => {
        console.error(error);
        this.isSearching = false;
        this.toastr.error('An unknown error occurred');
      }
    )
  }

  public filterChange() {
    let orderByKey: string;
    let reverse = false;
    if (this.filters.orderBy === 'Name') {
      orderByKey = 'Title';
    } else if (this.filters.orderBy === 'Seeders') {
      orderByKey = 'Seeders';
      reverse = true;
    } else if (this.filters.orderBy === 'Size') {
      orderByKey = 'Size';
      reverse = true;
    }
    this.results = _.orderBy(this.results, (result) => {
      return result[orderByKey];
    });
    if (reverse) {
      this.results = this.results.reverse();
    }
  }

  public downloadTorrent(result: any) {
    const torrent = SearchManualComponent._getTorrentLinkFromResult(result);
    this._downloading[torrent] = true;
    this.apiService.download(torrent, this.type).subscribe(
      (data) => {
        console.log(data);
        if (!data.success) {
          this.toastr.error(data.error_detail);
        } else {
          this.toastr.success(result.Title);
        }
        delete this._downloading[torrent];
      },
      (error) => {
        delete this._downloading[torrent];
        this.toastr.error('An unknown error occurred');
      },
    )
  }

  public isDownloading(result) {
    let torrent = SearchManualComponent._getTorrentLinkFromResult(result);
    return this._downloading.hasOwnProperty(torrent);
  }

  protected static _getTorrentLinkFromResult(result) {
    let torrent: string;
    if (result.MagnetUri) {
      torrent = result.MagnetUri;
    } else {
      torrent = result.Link;
    }
    return torrent;
  }

}
