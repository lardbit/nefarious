import {EMPTY} from 'rxjs';
import {ToastrService} from 'ngx-toastr';
import {ApiService} from '../api.service';
import {FormArray, FormBuilder, FormControl, Validators, FormRecord} from '@angular/forms';
import {Component, OnInit} from '@angular/core';
import {concat, Observable, Subscription} from 'rxjs';
import {tap} from 'rxjs/operators';
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {QualityProfilesComponent} from "./quality-profiles.component";

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {
  public users: any[];
  public form: FormRecord<any>;
  public isSaving = false;
  public isLoading = false;
  public isVerifyingJackettIndexers = false;
  public isLoadingUsers = false;
  public gitCommit = '';
  public authenticateOpenSubtitles$: Subscription;

  constructor(
    public apiService: ApiService,
    public toastr: ToastrService,
    public fb: FormBuilder,
    public modalService: NgbModal,
  ) {
  }

  ngOnInit() {
    const settings = this.apiService.settings || {};
    this.form = this.fb.group({
      'jackett_host': [settings['jackett_host'], Validators.required],
      'jackett_port': [settings['jackett_port'], Validators.required],
      'jackett_token': [settings['jackett_token'], Validators.required],
      'jackett_filter_index': [settings['jackett_filter_index']],
      'transmission_host': [settings['transmission_host'], Validators.required],
      'transmission_port': [settings['transmission_port'], Validators.required],
      'transmission_user': [settings['transmission_user']],
      'transmission_pass': [settings['transmission_pass']],
      'transmission_tv_download_dir': [settings['transmission_tv_download_dir'], Validators.required],
      'transmission_movie_download_dir': [settings['transmission_movie_download_dir'], Validators.required],
      'open_subtitles_username': [settings['open_subtitles_username']],
      'open_subtitles_password': [settings['open_subtitles_password']],
      'open_subtitles_auto': [settings['open_subtitles_auto']],
      'quality_profile_tv': [settings['quality_profile_tv'], Validators.required],
      'quality_profile_movies': [settings['quality_profile_movies'], Validators.required],
      'allow_hardcoded_subs': [settings['allow_hardcoded_subs'], Validators.required],
      'exclusions': [settings['keyword_search_filters'] ? Object.keys(settings['keyword_search_filters']) : []],
      'enable_video_detection': [settings['enable_video_detection'], Validators.required],
      'language': [settings['language'], Validators.required],
      'users': new FormArray([]),
      'apprise_notification_url': [settings['apprise_notification_url']],
      'preferred_media_category': [settings['preferred_media_category'], Validators.required],
      'stuck_download_handling_enabled': [settings['stuck_download_handling_enabled'], Validators.required],
      'stuck_download_handling_days': [settings['stuck_download_handling_days'], Validators.required],
    });

    this.isLoadingUsers = true;
    this.apiService.fetchUsers().subscribe(
      (users) => {
        this.users = users;
        this.users.forEach((user) => {
          const controls = {
            password: '',
          };
          Object.keys(user).forEach((key) => {
            controls[key] = new FormControl(user[key]);
          });
          this.form.controls.users.insert(0, this.fb.group(controls));
        });
      }, (error) => {
        this.toastr.error('An unknown error occurred loading users');
      }, () => {
        this.isLoadingUsers = false;
      }
    );

    this.apiService.fetchGitCommit().subscribe((data) => {
      this.gitCommit = data.commit;
    });
  }

  public submit(): void {
    this._saveSettings().subscribe();
  }

  public hasExclusions(): boolean {
    const exclusions = this.form.controls.exclusions.value;
    return exclusions && exclusions.length;
  }

  public saveAndVerifySettings() {
    this._saveSettings().pipe(
      tap((data) => {
        this._verifySettings();
      })
    ).subscribe();
  }

  public saveAndVerifyJackettIndexers() {
    this._saveSettings().pipe(
      tap((data) => {
        this._verifyJackettIndexers();
      })
    ).subscribe();
  }

  public qualityProfiles(): any[] {
    return this.apiService.qualityProfiles;
  }

  public mediaCategories(): string[] {
    return this.apiService.mediaCategories;
  }

  public addUser() {
    this.form.controls.users.push(this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required],
      can_immediately_watch_movies: [false],
      can_immediately_watch_tv_shows: [false],
    }));
  }

  public saveUser(index: number) {

    const userControl = this.form.controls.users.controls[index];
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
          console.error(error);
        }
      );
    } else {  // new user
      this.apiService.createUser(userControl.value.username, userControl.value.password).subscribe(
        (data) => {
          this.toastr.success(`Added ${userControl.value.username}`);
          this.form.controls.users.at(index).addControl('id', new FormControl(data.id));
        },
        (error) => {
          this.toastr.error(`An unknown error occurred adding user ${userControl.value.username}`);
          console.error(error);
        }
      );
    }
  }

  public removeUser(index: number) {
    const userControl = this.form.controls.users.controls[index];
    this.apiService.deleteUser(userControl.value.id).subscribe(
      (data) => {
        this.toastr.success(`Successfully deleted ${userControl.value.username}`);
        this.form.controls.users.removeAt(index);
      },
      (error) => {
        this.toastr.error(`An unknown error occurred deleting user ${userControl.value.username}`);
        console.error(error);
      }
    );
  }

  public canDeleteUser(index: number) {
    const userControl = this.form.controls.users.controls[index];
    return userControl.get('id') && this.apiService.user.id !== userControl.get('id').value;
  }

  public getLanguages() {
    return this.apiService.settings.tmdb_languages;
  }

  public importLibrary(mediaType) {
    this.apiService.importMedia(mediaType).subscribe(
      (data) => {
        this.toastr.success('Importing library...');
      }, (error) => {
        let message = 'Error importing library.';
        if (error.error && error.error.detail) {
          message = `${message} ${error.error.detail}`;
        }
        this.toastr.error(message);
      }
    );
  }

  public hostDownloadPath(): boolean {
    return this.apiService.settings.host_download_path;
  }

  public hasHostDownloadPath(): boolean {
    return Boolean(this.apiService.settings.host_download_path);
  }

  public authenticateOpenSubtitles() {
    const error_message = 'An unknown error occurred';
    const params = {};
    [
      'open_subtitles_auto',
      'open_subtitles_username',
      'open_subtitles_password',
    ].forEach((key) => {
      params[key] = this.form.value[key];
    });

    // save settings, auth with open subtitles, then fetch updated settings to get new user token
    this.authenticateOpenSubtitles$ = concat(
      this.apiService.updateSettings(this.apiService.settings.id, params),
      this.apiService.openSubtitlesAuth().pipe(
        tap((data: any) => {
          if (data.success) {
            this.toastr.success('Successfully authenticated with Open Subtitles');
          } else {
            this.toastr.error(data.error || error_message);
          }
        }),
      ),
      this.apiService.fetchSettings(),
    ).subscribe(
      (data: any) => {
      }, (error) => {
        console.error(error);
        this.toastr.error(error_message);
      }
    );
  }

  public queueTask(task: string): void {
    this.isLoading = true;
    this.apiService.queueTask(task).subscribe(
      (data) => {
        this.toastr.success(`Successfully queued task ${task}`);
        this.isLoading = false;
      }, (error => {
        this.toastr.error(`Error queueing task ${task}`);
        this.isLoading = false;
        console.error(error);
      })
    );
  }

  public sendTestNotification(): void {
    // save settings and then send test notification
    this._saveSettings().pipe(
      tap(() => {
        this.apiService.sendNotification(`Test message from nefarious [${new Date().getTime()}]`).subscribe(
          (data) => {
            if (data.success) {
              this.toastr.success('Successfully sent notification');
            } else {
              this.toastr.warning('Notification returned an error');
            }
          }, (error) => {
            this.toastr.error('An unknown error occurred sending notification');
          }
        );
      })
    ).subscribe();
  }

  public deleteBlacklists() {
    this.isSaving = true;
    this.apiService.deleteAllBlacklists().subscribe({
      complete: () => {
        this.toastr.success('Successfully deleted all blacklist entries');
        this.isSaving = false;
      },
      error: (error) => {
        console.error(error);
        this.toastr.error('An error occurred deleting blacklist entries');
        this.isSaving = false;
      }
    })
  }

  public manageQualityProfiles() {
    this.modalService.open(QualityProfilesComponent, {
      size: "lg",
      scrollable: true,
    });
  }

  protected _saveSettings(): Observable<any> {
    this.isSaving = true;

    // validate form and display errors
    if (!this.form.valid) {
      Object.keys(this.form.controls).forEach((key) => {
        const control = this.form.get(key);
        if (control.errors) {
          const errors = [];
          Object.keys(control.errors).forEach((errorKey) => {
            errors.push(`${errorKey}: ${control.errors[errorKey]}`);
          });
          this.toastr.error(`${key}: ${errors.join(', ')}`);
        }
      });
      this.isSaving = false;
      return EMPTY;
    }

    // create a copy of the form data so we can modify it
    const formData = Object.assign({}, this.form.value);

    // handle keyword exclusions
    const exclusions = {};
    formData['exclusions'].forEach((exclusion) => {
      exclusions[exclusion] = false;
    });
    formData['keyword_search_filters'] = exclusions;
    delete formData['exclusions'];

    return this.apiService.updateSettings(this.apiService.settings.id, formData).pipe(
      tap(
        (data) => {
          this.toastr.success('Updated settings');
          this.isSaving = false;
        },
        (error) => {
          console.error(error);
          this.toastr.error(JSON.stringify(error.error));
          this.isSaving = false;
        }
      ),
    );
  }

  protected _verifySettings(): void {
    this.isSaving = true;
    this.apiService.verifySettings().subscribe(
      (data) => {
        let hasErrors = false;
        // verify individual indexers
        data.jackett.Indexers.forEach((indexer) => {
          if (indexer.Error) {
            hasErrors = true;
            this.toastr.error(
              `Indexer "${indexer.Name}" returned an error.  See browser console and/or reconfigure Jackett for this indexer`);
            console.error(indexer.Error);
          }
        });
        if (hasErrors) {
          this.toastr.error('Settings are invalid');
        } else {
          this.toastr.success('Settings are valid');
        }
        this.isSaving = false;
      },
      (error) => {
        console.error(error);
        this.toastr.error(JSON.stringify(error.error));
        this.isSaving = false;
      },
    );
  }

  protected _verifyJackettIndexers() {
    this.isVerifyingJackettIndexers = true;
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
        this.isVerifyingJackettIndexers = false;
      },
      (error) => {
        this.toastr.error('An unknown error occurred verifying jackett indexers');
        this.isVerifyingJackettIndexers = false;
      },
    );
  }
}
