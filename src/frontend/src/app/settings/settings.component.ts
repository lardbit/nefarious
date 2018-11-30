import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { FormBuilder, Validators} from '@angular/forms';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {
  public form;
  public isSaving = false;

  constructor(
    private toastr: ToastrService,
    private apiService: ApiService,
    private fb: FormBuilder,
  ) { }

  ngOnInit() {
    const settings = this.apiService.settings || {};
    this.form = this.fb.group({
      'jackett_host': [settings['jackett_host'], Validators.required],
      'jackett_port': [settings['jackett_port'], Validators.required],
      'jackett_token': [settings['jackett_token'], Validators.required],
      'transmission_host': [settings['transmission_host'], Validators.required],
      'transmission_port': [settings['transmission_port'], Validators.required],
      'transmission_user': [settings['transmission_user'], Validators.required],
      'transmission_pass': [settings['transmission_pass'], Validators.required],
      'transmission_tv_download_dir': [settings['transmission_tv_download_dir'], Validators.required],
      'transmission_movie_download_dir': [settings['transmission_movie_download_dir'], Validators.required],
      'tmdb_token': [settings['tmdb_token'], Validators.required],
      'quality_profile': [settings['quality_profile'], Validators.required],
    });
  }

  public onSubmit() {
    this.isSaving = true;

    let observable: Observable<any>;

    console.log('submitting', this.form.value);

    if (this.apiService.settings) {
      observable = this.apiService.updateSettings(this.apiService.settings.id, this.form.value);
    } else {
      observable = this.apiService.createSettings(this.form.value);
    }

    observable.subscribe(
      (data) => {
        this.toastr.success('Updated settings');
        this.isSaving = false;
      },
      (error) => {
        console.log(error);
        this.toastr.error(JSON.stringify(error.error));
        this.isSaving = false;
      }
    );
  }

  public verifySettings() {
    this.isSaving = true;
    this.apiService.verifySettings().subscribe(
      (data) => {
        this.toastr.success('Settings appear valid');
        this.isSaving = false;
      },
      (error) => {
        console.error(error);
        this.toastr.error(JSON.stringify(error.error));
        this.isSaving = false;
      },
    );
  }

  public qualityProfiles(): string[] {
    return this.apiService.settings.quality_profiles;
  }
}
