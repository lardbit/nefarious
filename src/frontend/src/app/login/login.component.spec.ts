import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { LoginComponent } from './login.component';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import { StorageMap } from '@ngx-pwa/local-storage';
import { of } from 'rxjs';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

class MockStorageMap {
  get(_key: string) { return of(null); }
  set(_key: string, _val: any) { return of(undefined); }
}

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let mockApiService: any;
  let mockRouter: jasmine.SpyObj<Router>;
  let mockToastr: any;

  beforeEach(waitForAsync(() => {
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockToastr = jasmine.createSpyObj('ToastrService', ['success', 'error']);
    mockApiService = {
      login: () => of({ token: 'abc' }),
      fetchUser: () => of([{ id: 1 }]),
      fetchCoreData: () => of({}),
      fetchWatchMedia: () => of([]),
    };

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, ReactiveFormsModule],
      declarations: [LoginComponent],
      providers: [
        { provide: ApiService, useValue: mockApiService },
        { provide: Router, useValue: mockRouter },
        { provide: ToastrService, useValue: mockToastr },
        { provide: StorageMap, useClass: MockStorageMap },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      teardown: { destroyAfterEach: false }
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have a form with username and password controls', () => {
    expect(component.form).toBeTruthy();
    expect(component.form.get('username')).toBeTruthy();
    expect(component.form.get('password')).toBeTruthy();
  });

  it('should require username and password', () => {
    expect(component.form.valid).toBeFalse();
    component.form.patchValue({ username: 'admin', password: 'pass' });
    expect(component.form.valid).toBeTrue();
  });

  it('should render username and password inputs', () => {
    const el = fixture.nativeElement;
    expect(el.querySelector('input[formControlName="username"]')).toBeTruthy();
    expect(el.querySelector('input[formControlName="password"]')).toBeTruthy();
  });

  it('should call apiService.login on submit', () => {
    spyOn(mockApiService, 'login').and.returnValue(of({ token: 'abc' }));
    component.form.patchValue({ username: 'admin', password: 'pass' });
    component.onSubmit();
    expect(mockApiService.login).toHaveBeenCalledWith('admin', 'pass');
  });

  it('should navigate to /search on successful login', () => {
    component.form.patchValue({ username: 'admin', password: 'pass' });
    component.onSubmit();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/search']);
    expect(mockToastr.success).toHaveBeenCalled();
  });

  it('should render loading indicator', () => {
    component.isSaving = true;
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.querySelector('ngx-loading')).toBeTruthy();
  });
});
