import {Component, OnInit} from '@angular/core';
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {ApiService} from "../api.service";
import {FormArray, FormBuilder, FormControl, FormGroup, Validators} from "@angular/forms";
import {ToastrService} from 'ngx-toastr';

// TODO - add/remove profiles

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
      profiles: this.fb.array(this.apiService.qualityProfiles.map(p => this.fb.group({
        id: p.id,
        name: this.fb.control(p.name, [Validators.required, Validators.minLength(2)]),
        quality: this.fb.control(p.quality, [Validators.required]),
        min_size_gb: this.fb.control(p.min_size_gb, [Validators.min(0)]),
        max_size_gb: this.fb.control(p.max_size_gb, [Validators.min(0)]),
        require_hdr: p.require_hdr,
        require_five_point_one: p.require_five_point_one,
      }))),
    });
  }

  public save(profileFormGroup: FormGroup) {
    this.isLoading = true;
    const data = profileFormGroup.value;
    this.apiService.updateQualityProfile(data.id, data).subscribe({
      next: () => {
        this.toastr.success('Successfully updated quality profile');
        this.isLoading = false;
      },
      error: (error) => {
        console.error(error);
        this.toastr.error('An unknown error occurred updating the quality profile');
        this.isLoading = false;
      }
    })
  }

  public delete(formArrayIndex: number) {
    const profileFormGroup = this.form.controls.profiles.controls[formArrayIndex];
    this.isLoading = true;
    const data = profileFormGroup.value;
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
}
