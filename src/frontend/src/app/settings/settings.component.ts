import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { FormArray, FormBuilder, FormControl, Validators } from '@angular/forms';
import { Component, OnInit } from '@angular/core';
import * as _ from 'lodash';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {
  public users: any[];
  public form;
  public isSaving = false;
  public isVeryingJackettIndexers = false;
  public gitCommit = '';

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
      'transmission_user': [settings['transmission_user']],
      'transmission_pass': [settings['transmission_pass']],
      'transmission_tv_download_dir': [settings['transmission_tv_download_dir'], Validators.required],
      'transmission_movie_download_dir': [settings['transmission_movie_download_dir'], Validators.required],
      'quality_profile_tv': [settings['quality_profile_tv'], Validators.required],
      'quality_profile_movies': [settings['quality_profile_movies'], Validators.required],
      'allow_hardcoded_subs': [settings['allow_hardcoded_subs'], Validators.required],
      'exclusions': [settings['keyword_search_filters'] ? _.keys(settings['keyword_search_filters']) : []],
      'language': [settings['language'], Validators.required],
      'users': new FormArray([]),
      'webhook_url': [settings['webhook_url']],
      'webhook_key': [settings['webhook_key']],
    });

    this.apiService.fetchUsers().subscribe(
      (users) => {
        this.users = users;
        this.users.forEach((user) => {
          const controls = {
            password: '',
          };
          _.forOwn(user, (value, key) => {
            controls[key] = new FormControl(value);
          });
          this.form.get('users').insert(0, this.fb.group(controls));
        });
      }
    );

    this.apiService.fetchGitCommit().subscribe((data) => {
      this.gitCommit = data.commit;
    });
  }

  public submit() {
    this.isSaving = true;

    // create a copy of the form data so we can modify it
    const formData = _.assign({}, this.form.value);

    // handle keyword exclusions
    const exclusions = {};
    _.forEach(formData['exclusions'], (exclusion) => {
      exclusions[exclusion] = false;
    });
    formData['keyword_search_filters'] = exclusions;
    delete formData['exclusions'];

    this.apiService.updateSettings(this.apiService.settings.id, formData).subscribe(
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

  public hasExclusions(): boolean {
    const exclusions = this.form.get('exclusions').value;
    return exclusions && exclusions.length;
  }

  public verifySettings() {
    this.isSaving = true;
    this.apiService.verifySettings().subscribe(
      (data) => {
        this.toastr.success('Settings are valid');
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

  public addUser() {
    this.form.get('users').push(this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
      can_immediately_watch_movies: [false],
      can_immediately_watch_tv_shows: [false],
    }));
  }

  public saveUser(index: number) {

    const userControl = this.form.get('users').controls[index];
    if (!userControl.valid) {
      this.toastr.error('Please supply all required fields for this user');
      return;
    }

    // existing user
    if (userControl.value.id) {
      this.apiService.updateUser(userControl.value.id, userControl.value).subscribe(
        (data) => {
          this.toastr.success(`Successfully updated user ${userControl.value.username}`);
        },
        (error) => {
          this.toastr.error(`An unknown error occurred updating user ${userControl.value.username}`);
          console.log(error);
        }
      );
    } else {  // new user
      this.apiService.createUser(userControl.value.username, userControl.value.password).subscribe(
        (data) => {
          this.toastr.success(`Added ${userControl.value.username}`);
          this.form.get('users').at(index).addControl('id', new FormControl(data.id));
        },
        (error) => {
          this.toastr.error(`An unknown error occurred adding user ${userControl.value.username}`);
          console.log(error);
        }
      );
    }
  }

  public removeUser(index: number) {
    const userControl = this.form.get('users').controls[index];
    this.apiService.deleteUser(userControl.value.id).subscribe(
      (data) => {
        this.toastr.success(`Successfully deleted ${userControl.value.username}`);
        this.form.get('users').removeAt(index);
      },
      (error) => {
        this.toastr.error(`An unknown error occurred deleting user ${userControl.value.username}`);
        console.log(error);
      }
    );
  }

  public canDeleteUser(index: number) {
    const userControl = this.form.get('users').controls[index];
    return userControl.get('id') && this.apiService.user.id !== userControl.get('id').value;
  }

  public getLanguages() {
    return this.apiService.settings.tmdb_languages;
  }
}
