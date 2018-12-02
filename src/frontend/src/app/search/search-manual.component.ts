import { Component, OnInit } from '@angular/core';
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
  protected _downloading: any = {};

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    ) {
  }

  ngOnInit() {
  }

  public filterChange() {
    let orderByKey: string;
    let reverse = false;
    if (this.filters.orderBy == 'Name') {
      orderByKey = 'Title';
    } else if (this.filters.orderBy == 'Seeders') {
      orderByKey = 'Seeders';
      reverse = true;
    } else if (this.filters.orderBy == 'Size') {
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

  public searchTorrents() {
    this.results = [];
    this.isSearching = true;
    this.apiService.searchTorrents(this.apiService.searchQuery.query, this.apiService.searchQuery.type).subscribe(
      (results) => {
        console.log(results);
        this.results = results.Results;
        this.filterChange();
        this.isSearching = false;
      }, (error) => {
        this.isSearching = false;
        this.toastr.error('An unknown error occurred');
      }
    )
  }

  public downloadTorrent(result: any) {
    let torrent = SearchManualComponent._getTorrentLinkFromResult(result);
    this._downloading[torrent] = true;
    this.apiService.download(torrent).subscribe(
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
