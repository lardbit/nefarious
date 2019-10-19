import { ToastrService } from 'ngx-toastr';
import { Router } from '@angular/router';
import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class SettingsGuard implements CanActivate {

  constructor(
    private apiService: ApiService,
    private router: Router,
    private toastr: ToastrService,
  ) {
  }

  canActivate(
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean> | Promise<boolean> | boolean {

    //
    // verify settings
    //

    // TODO - verify the jackett api token isn't the default

    if (!this.apiService.settings) {
      this.toastr.error('missing core settings');
        console.log('no settings, redirecting');
      return false;
    }

    return true;
  }
}
