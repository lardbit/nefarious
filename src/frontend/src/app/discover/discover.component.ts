import { Component, OnInit } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import {log} from "util";

@Component({
  selector: 'app-discover',
  templateUrl: './discover.component.html',
  styleUrls: ['./discover.component.css']
})
export class DiscoverComponent implements OnInit {
  public results: any[];

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
  ) { }

  ngOnInit() {
  }

  public submit() {
    const params = {
      sort_by: 'popularity.desc',
    };
    this.apiService.discoverMovies(params).subscribe(
      (data: any) => {
        this.results = data.results;
      },
      (error) => {
        console.error(error);
        this.toastr.error('An unknown error occured');
      }
    )
  }

}
