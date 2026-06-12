import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { RottenTomatoesComponent } from './rotten-tomatoes.component';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import { StorageMap } from '@ngx-pwa/local-storage';
import { MockStorageMap, createMockApiService } from '../test-helpers';

describe('RottenTomatoesComponent', () => {
  let component: RottenTomatoesComponent;
  let fixture: ComponentFixture<RottenTomatoesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, ReactiveFormsModule],
      declarations: [RottenTomatoesComponent],
      providers: [
        { provide: ApiService, useValue: createMockApiService() },
        { provide: ToastrService, useValue: jasmine.createSpyObj('ToastrService', ['success', 'error', 'info']) },
        { provide: StorageMap, useClass: MockStorageMap },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      teardown: { destroyAfterEach: false }
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RottenTomatoesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
