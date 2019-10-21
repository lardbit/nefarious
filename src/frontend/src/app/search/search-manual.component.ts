import { Component, Input, Output, OnInit, EventEmitter } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import * as _ from 'lodash';


@Component({
  selector: 'app-search-manual',
  templateUrl: './search-manual.component.html',
  styleUrls: ['./search-manual.component.css']
})
export class SearchManualComponent implements OnInit {
  @Input('tmdbMedia') tmdbMedia;
  @Input('tmdbTVSeason') tmdbTVSeason;
  @Input('tmdbTVEpisode') tmdbTVEpisode;
  @Input('mediaType') mediaType: string;
  @Output() downloaded = new EventEmitter<any>();
  public searchInput: string;
  public orderByOptions = ['Name', 'Seeders', 'Size'];
  public results: any[] = [];
  public isSearching = false;
  public isDownloading = false;
  public filter = '';
  public filters: {
    orderBy: string,
  } = {
    orderBy: 'Name',
  };

  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private toastr: ToastrService,
    ) {
  }

  ngOnInit() {
    // automatically search on load
    this.searchInput = this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? this.tmdbMedia.name : this.tmdbMedia.title;
    this.search();
  }

  public search() {
    this.results = [];
    this.isSearching = true;
    this.apiService.searchTorrents(this.searchInput, this.mediaType).subscribe(
      (results) => {
        this.results = results;
        this.filterChange();
        this.isSearching = false;
      }, (error) => {
        console.error(error);
        this.isSearching = false;
        this.toastr.error('An unknown error occurred');
      }
    );
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

  public downloadTorrent(torrentResult: any, tmdbMedia: any) {
    this.isDownloading = true;
    const params = {};
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
      params['season_number'] = this.tmdbTVSeason.season_number;
      // requesting a single episode
      if (this.tmdbTVEpisode) {
        params['episode_number'] = this.tmdbTVEpisode.episode_number;
      }
    }
    this.apiService.download(torrentResult, this.mediaType, tmdbMedia, params).subscribe(
      (data) => {
        if (data.success) {
          let title;
          if (data.watch_tv_episode) {
            title = data.watch_tv_episode.name;
          } else if (data.watch_tv_season_request) {
            title = data.watch_tv_season_request.name;
          } else if (data.watch_movie) {
            title = data.watch_movie.name;
          }
          this.toastr.success(title);
          this.isDownloading = false;
          this.downloaded.emit(true);
        } else {
          this.toastr.error(data.error_detail);
        }
      },
      (error) => {
        this.toastr.error('An unknown error occurred');
      },
    );
  }

  public getTmdbTitle() {
    if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE) {
      return this.tmdbMedia.title;
    } else {
      // single episode
      if (this.tmdbTVEpisode) {
        return `${this.tmdbMedia.name}  ${this.tmdbTVSeason.season_number}x${this.tmdbTVEpisode.episode_number}`;
      } else {
        // full season
        return `${this.tmdbMedia.name} - Season ${this.tmdbTVSeason.season_number}`;
      }
    }
  }
}
