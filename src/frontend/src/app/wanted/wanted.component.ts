import { Component, OnInit } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { merge } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-wanted',
  templateUrl: './wanted.component.html',
  styleUrls: ['./wanted.component.css']
})
export class WantedComponent implements OnInit {

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
  ) {}

  ngOnInit() {
    merge(
      this.apiService.fetchWantedMovies().pipe(
        map((data) => {
          console.log('wanted movies', data);
        }),
      ),
      this.apiService.fetchWantedTVSeasons().pipe(
        map((data) => {
          console.log('wanted seasons', data);
        }),
      ),
      this.apiService.fetchWantedTVEpisodes().pipe(
        map((data) => {
          console.log('wanted episodes', data);
        }),
      ),
    ).subscribe(
      (data) => undefined,
      (error) => {
        console.error(error);
        this.toastr.error('An unknown error occurred');
      }
    );
  }

}
