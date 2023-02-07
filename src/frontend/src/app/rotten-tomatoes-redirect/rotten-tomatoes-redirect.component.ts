import { ActivatedRoute, Router } from '@angular/router';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-rotten-tomatoes-redirect',
  templateUrl: './rotten-tomatoes-redirect.component.html',
  styleUrls: ['./rotten-tomatoes-redirect.component.css']
})
export class RottenTomatoesRedirectComponent implements OnInit {
  public isLoading = true;
  public title: string;
  public mediaType: string;
  public results: any[];

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private apiService: ApiService,
    private toastr: ToastrService,
  ) { }

  ngOnInit(): void {
    this.title = this.route.snapshot.params['title'];
    this.mediaType = this.route.snapshot.params['mediaType'];

    this.isLoading = true;
    this.apiService.searchMedia(this.title, this.mediaType).subscribe(
      (data) => {
        if (data.results && data.results.length > 0) {
          // try and find an exact match, otherwise fallback to first result
          let match = data.results.find((movie) => {
            return movie.title === this.title;
          });
          // perfect match so redirect to media
          if (match) {
            this.router.navigate(['/media', this.mediaType, match.id], { replaceUrl: true });  // no history so we can go "backwards"
          } else { // display results so user can choose
            this.results = data.results;
          }
        } else {
          this.toastr.error('No results found for title in TMDB');
        }
      },
      (error) => {
        console.error(error);
        this.toastr.error('An unknown error occurred');
        this.isLoading = false;
      },
      () => {
        this.isLoading = false;
      },
    );
  }
}
