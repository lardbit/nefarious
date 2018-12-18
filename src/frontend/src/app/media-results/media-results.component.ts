import { Component, OnInit, Input } from '@angular/core';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-media-results',
  templateUrl: './media-results.component.html',
  styleUrls: ['./media-results.component.css']
})
export class MediaResultsComponent implements OnInit {
  @Input() results: any[];
  @Input() mediaType: string;
  public search = '';

  constructor(
    private apiService: ApiService,
  ) {
  }

  ngOnInit() {
  }

  public isSearchingTV() {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV;
  }

  public isSearchingMovies() {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_MOVIE;
  }

  public mediaPosterURL(result) {
    return `${this.apiService.settings.tmdb_configuration.images.base_url}/original/${result.poster_path}`;
  }
}
