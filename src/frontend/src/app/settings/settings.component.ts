import { ToastrService } from 'ngx-toastr';
import { ApiService } from '../api.service';
import { FormArray, FormBuilder, FormControl, Validators } from '@angular/forms';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
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
      'jackett': this.fb.group({
          'jackett_host': [settings['jackett_host'], Validators.required],
          'jackett_port': [settings['jackett_port'], Validators.required],
          'jackett_token': [settings['jackett_token'], Validators.required],
        }
      ),
      'transmission': this.fb.group({
        'transmission_host': [settings['transmission_host'], Validators.required],
        'transmission_port': [settings['transmission_port'], Validators.required],
        'transmission_user': [settings['transmission_user']],
        'transmission_pass': [settings['transmission_pass']],
        'transmission_tv_download_dir': [settings['transmission_tv_download_dir'], Validators.required],
        'transmission_movie_download_dir': [settings['transmission_movie_download_dir'], Validators.required],
      }),
      'quality': this.fb.group({
          'quality_profile_tv': [settings['quality_profile_tv'], Validators.required],
          'quality_profile_movies': [settings['quality_profile_movies'], Validators.required],
      }),
      'subs': this.fb.group({
        'allow_hardcoded_subs': [settings['allow_hardcoded_subs'], Validators.required],
      }),
      'users': new FormArray([]),
    });

    if (this.apiService.settings) {
      this.apiService.fetchJackettIndexers().subscribe(
        (data: string[]) => {
          this.jackettIndexers = data;
          const formControls = {};
          this.jackettIndexers.forEach((indexer) => {
            formControls[indexer] = (
              this.apiService.settings.jackett_indexers_seed && this.apiService.settings.jackett_indexers_seed[indexer]
            ) || false;
          });
          this.form.get('jackett').addControl('jackett_indexers_seed', this.fb.group(formControls));
          this.isLoadingJackettIndexers = false;
        },
        (error) => {
          console.error(error);
          this.toastr.error('An unknown error occurred fetching jackett indexers');
          this.isLoadingJackettIndexers = false;
        }
      );
    }

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
  }

  public submit(group: string) {
    this.isSaving = true;

    let observable: Observable<any>;

    // settings
    if (this.apiService.settings) {
      observable = this.apiService.updateSettings(this.apiService.settings.id, this.form.get(group).value);
    } else {
      observable = this.apiService.createSettings(this.form.get(group).value);
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

  public hasSettings() {
    return !!this.apiService.settings;
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
      )
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
      )
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
    )
  }

  public canDeleteUser(index: number) {
    const userControl = this.form.get('users').controls[index];
    return userControl.get('id') && this.apiService.user.id !== userControl.get('id').value;
  }
}
