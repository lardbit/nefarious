import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { FormBuilder, Validators} from '@angular/forms';
import { Component, OnInit } from '@angular/core';
import { ApiService } from '../api.service';
import { forkJoin} from 'rxjs';
import { first, mergeMap } from 'rxjs/operators';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  public form;
  public isSaving = false;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private toastr: ToastrService,
    private router: Router,
  ) { }

  ngOnInit() {
    this.form = this.fb.group({
      'username': ['', Validators.required],
      'password': ['', Validators.required],
    });
  }

  public onSubmit() {
    this.isSaving = true;
    this.apiService.login(this.form.value.username, this.form.value.password).pipe(
      mergeMap((data) => {
        return forkJoin(
          this.apiService.fetchUser(),
          this.apiService.fetchCoreData(),
        );
      }),
      first(),
      ).subscribe(
      (data) => {
        console.log('Retrieved api token');
        this.isSaving = false;
        this.toastr.success('Successfully logged in');
        this.router.navigate(['/search']);
      },
      (error) => {
        this.toastr.error(JSON.stringify(error.error));
        console.log(error);
        this.isSaving = false;
      }
    );
  }
}
