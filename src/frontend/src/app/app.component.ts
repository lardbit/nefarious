import { ToastrService } from 'ngx-toastr';
import { Component, OnInit } from '@angular/core';
import { ApiService } from './api.service';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  public isCollapsed = true;

  constructor(
    private apiService: ApiService,
    private toastr: ToastrService,
  ) {
  }

  ngOnInit() {
  }

  public isStaff() {
    return this.apiService.user && this.apiService.user.is_staff;
  }

  public isLoggedIn() {
    return this.apiService.isLoggedIn();
  }

  public getUserName() {
    return this.apiService.user ? this.apiService.user.username : '';
  }

  public toggleCollapseNav() {
    this.isCollapsed = !this.isCollapsed;
  }

  public collapseNav() {
    this.isCollapsed = true;
  }
}
