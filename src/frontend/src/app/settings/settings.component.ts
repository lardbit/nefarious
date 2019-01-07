import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { FormBuilder, Validators } from '@angular/forms';
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
  public jackettIndexers: string[];
  public isJackettIndexersSettingsCollapsed = true;
  public isLoadingJackettIndexers = true;
  public isVeryingJackettIndexers = false;

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
      'quality_profile_tv': [settings['quality_profile_tv'], Validators.required],
      'quality_profile_movies': [settings['quality_profile_movies'], Validators.required],
    });

    this.apiService.fetchJackettIndexers().subscribe(
      (data: string[]) => {
        this.jackettIndexers = data;
        const formControls = {};
        this.jackettIndexers.forEach((indexer) => {
          formControls[indexer] = (
            this.apiService.settings.jackett_indexers_seed && this.apiService.settings.jackett_indexers_seed[indexer]
          ) || false;
        });
        this.form.addControl('jackett_indexers_seed', this.fb.group(formControls));
        this.isLoadingJackettIndexers = false;
      },
      (error) => {
        console.error(error);
        this.toastr.error('An unknown error occurred fetching jackett indexers');
        this.isLoadingJackettIndexers = false;
      }
    );
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
    return this.apiService.qualityProfiles;
  }

  public verifyJackettIndexers() {
    this.isVeryingJackettIndexers = true;
    this.apiService.verifyJackettIndexers().subscribe(
      (data: any[]) => {
        const failedIndexers = data.filter((indexer: any) => {
          return indexer.Error;
        });
        if (failedIndexers.length) {
          failedIndexers.forEach((failedIndexer: any) => {
            this.toastr.error(failedIndexer.Error.substring(0, 200), failedIndexer.Name);
          });
        } else {
          this.toastr.success('All indexers were successful');
        }
        this.isVeryingJackettIndexers = false;
      },
      (error) => {
        this.toastr.error('An unknown error occurred verifying jackett indexers');
        this.isVeryingJackettIndexers = false;
      },
    );
  }
}
