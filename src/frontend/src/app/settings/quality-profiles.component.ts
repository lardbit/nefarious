import {Component, OnInit} from '@angular/core';
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {ApiService} from "../api.service";
import {FormArray, FormBuilder, FormGroup, Validators} from "@angular/forms";
import {ToastrService} from 'ngx-toastr';
import {Observable} from "rxjs";


@Component({
  selector: 'app-quality-profiles',
  templateUrl: './quality-profiles.component.html',
  styleUrl: './quality-profiles.component.css'
})
export class QualityProfilesComponent implements OnInit {
  public isLoading = false;
  public form: FormGroup<{ profiles: FormArray<FormGroup> }>;

  constructor(
    public apiService: ApiService,
    public activeModal: NgbActiveModal,
    public fb: FormBuilder,
    public toastr: ToastrService,
  ) {
  }

  ngOnInit() {
    this.form = this.fb.group({
      profiles: this.fb.array(this.apiService.qualityProfiles.map(p => this._getNewFormGroup(p))),
    });
  }

  public add() {
    this.form.controls.profiles.insert(0, this._getNewFormGroup());
  }

  public save(profileFormGroup: FormGroup) {
    this.isLoading = true;
    let update$: Observable<any>;
    let updateVerb: string;
    const data = profileFormGroup.value;
    // update
    if (data.id) {
      update$ = this.apiService.updateQualityProfile(data.id, data);
      updateVerb = 'updated';
    }
    // create
    else {
      update$ = this.apiService.createQualityProfile(data);
      updateVerb = 'created';
    }
    update$.subscribe({
      next: () => {
        this.toastr.success(`Successfully ${updateVerb} quality profile`);
        this.isLoading = false;
      },
      error: (error) => {
        console.error(error);
        let msg: string;
        // display specific error
        if (error.error) {
          msg = Object.entries(error.error).map(([key,value]: [k: string, v: string[]]) => {
            return `${key}: ${value.join(', ')}`;
          }).join(', ');
        }
        // display generic error
        else {
          msg = 'An unknown error occurred updating the quality profile'
        }
        this.toastr.error(msg);
        this.isLoading = false;
      }
    })
  }

  public delete(formArrayIndex: number) {
    const profileFormGroup = this.form.controls.profiles.controls[formArrayIndex];
    const data = profileFormGroup.value;

    // remove unsaved form control
    if (!data.id) {
      this.form.controls.profiles.removeAt(formArrayIndex);
      return;
    }

    this.isLoading = true;

    // delete existing record
    this.apiService.deleteQualityProfile(data.id).subscribe({
      next: () => {
        // remove form group
        this.form.controls.profiles.removeAt(formArrayIndex);
        this.toastr.success('Successfully deleted quality profile');
        this.isLoading = false;
      },
      error: (error) => {
        // display specific error message if it exists
        if (error?.error?.message) {
          this.toastr.error(error.error.message);
        } else {
          this.toastr.error('An unknown error occurred deleting the quality profile');
        }
        console.error(error);
        this.isLoading = false;
      }
    })
  }

  protected _getNewFormGroup(data?: any): FormGroup {
    return this.fb.group({
      id: data?.id,
      name: this.fb.control(data?.name, [Validators.required, Validators.minLength(2)]),
      quality: this.fb.control(data?.quality, [Validators.required]),
      min_size_gb: this.fb.control(data?.min_size_gb, [Validators.min(0)]),
      max_size_gb: this.fb.control(data?.max_size_gb, [Validators.min(0)]),
      require_hdr: data?.require_hdr,
      require_five_point_one: data?.require_five_point_one,
    })
  }
}
