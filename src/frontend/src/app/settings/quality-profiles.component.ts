import {Component, OnInit} from '@angular/core';
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {ApiService} from "../api.service";
import {FormArray, FormBuilder, FormGroup, Validators} from "@angular/forms";
import {ToastrService} from 'ngx-toastr';

// TODO - add/remove profiles
// TODO - implement UI (html & angular) validation

@Component({
  selector: 'app-quality-profiles',
  templateUrl: './quality-profiles.component.html',
  styleUrl: './quality-profiles.component.css'
})
export class QualityProfilesComponent implements OnInit {

  public form: FormGroup<{ profiles: FormArray }>;

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
        profile: this.fb.control(p.profile, [Validators.required]),
        min_size_gb: this.fb.control(p.min_size_gb, [Validators.min(0)]),
        max_size_gb: this.fb.control(p.max_size_gb, [Validators.min(0)]),
        require_hdr: p.require_hdr,
        require_five_point_one: p.require_five_point_one,
      }))),
    });

    this.form.valueChanges.subscribe({
      next: (data) => {
        console.log(data);
      }
    })
  }

  public save() {
    // TODO - implement save
    this.toastr.error('SAVE TODO')
    this.activeModal.close()
  }
}
