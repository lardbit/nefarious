import { Component, OnInit } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { ActivatedRoute } from '@angular/router';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-wanted',
  templateUrl: './wanted.component.html',
  styleUrls: ['./wanted.component.css']
})
export class WantedComponent implements OnInit {
  public isLoading = true;
  public results: any[] = [];
  public mediaType: string;
  public alertMessage = '';

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {

    this.route.params.subscribe(
      (params) => {
        this.results = [];
        this.mediaType = params.type;
        let wanted;
        if (this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV) {
          wanted = forkJoin(
            this.apiService.fetchWantedTVSeasons(),
            this.apiService.fetchWantedTVEpisodes(),
          );
        } else {
          wanted = forkJoin(this.apiService.fetchWantedMovies());
        }

        wanted.subscribe(
          (data) => {
            for (const results of data) {
              this.results = this.results.concat(results);
            }
            if (this.results.length <= 0) {
              this.alertMessage = 'You have everything you want. Wow.';
            } else {
              this.alertMessage = '';
            }
            this.isLoading = false;
          },
          (error) => {
            console.error(error);
            this.toastr.error('An unknown error occurred');
            this.isLoading = false;
          }
        );
      }
    );
  }

  public getTMDBId(result) {
    return this.mediaType === this.apiService.SEARCH_MEDIA_TYPE_TV ? result['tmdb_show_id'] : result['tmdb_movie_id'];
  }

}
