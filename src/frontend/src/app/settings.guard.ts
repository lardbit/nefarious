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
    // settings will have already been created and all fields were created using their defaults.
    // however, the jackett api token used a dummy value and needs to be defined so we're checking
    // for that scenario
    //

    // verify the jackett api token isn't the default
    if (this.apiService.settings) {
      if (this.apiService.settings.jackett_token === this.apiService.settings.jackett_default_token) {
        console.log('missing jackett token, redirecting');
        if (this.apiService.userIsStaff()) {
          this.toastr.error('missing jackett api token');
          this.router.navigate(['/settings']);
        } else {
          this.router.navigate(['/page-not-found']);
          this.toastr.error('missing jackett api token - contact admin');
        }
        return false;
      }
    }

    return true;
  }
}
