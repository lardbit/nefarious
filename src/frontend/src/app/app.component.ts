import { Component, OnInit } from '@angular/core';
import { ApiService } from './api.service';
import { OnPageVisible } from 'angular-page-visibility';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  public isCollapsed = true;

  constructor(
    private apiService: ApiService,
  ) {
  }

  ngOnInit() {
  }

  @OnPageVisible()
  logWhenPageVisible (): void {
    console.log('page visible, re-fetching data');
    this.apiService.fetchCoreData().subscribe();
  }

  public isStaff(): Boolean {
    return this.apiService.user && this.apiService.user.is_staff;
  }

  public isLoggedIn(): Boolean {
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
