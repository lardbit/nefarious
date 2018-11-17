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

    if (!this.apiService.settings) {
      // redirect to the settings page if they're privileged
      if (this.apiService.user && this.apiService.user.is_staff) {
        console.log('no settings, redirecting');
        this.router.navigate(['/settings']);
      } else {
        this.toastr.error('missing core settings - contact administrator');
      }
      return false;
    }

    return true;
  }
}
