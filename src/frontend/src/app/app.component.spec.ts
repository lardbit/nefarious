import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NgbCollapseModule, NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from './api.service';
import { of } from 'rxjs';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { StorageMap } from '@ngx-pwa/local-storage';

class MockStorageMap {
  get(_key: string) { return of(null); }
  set(_key: string, _val: any) { return of(undefined); }
}

describe('AppComponent', () => {
  let component: AppComponent;
  let fixture: ComponentFixture<AppComponent>;
  let mockApiService: any;

  beforeEach(waitForAsync(() => {
    mockApiService = {
      user: null,
      isLoggedIn: () => false,
      fetchCoreData: () => of(null),
      fetchWatchMedia: () => of(null),
      settings: { websocket_url: 'ws://localhost:8000/ws' },
    };

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, NgbCollapseModule, NgbDropdownModule],
      declarations: [AppComponent],
      providers: [
        { provide: ApiService, useValue: mockApiService },
        { provide: StorageMap, useClass: MockStorageMap },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      teardown: { destroyAfterEach: false }
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display app title "nefarious"', () => {
    const el = fixture.nativeElement;
    const brand = el.querySelector('.navbar-brand');
    expect(brand).toBeTruthy();
    expect(brand.textContent).toContain('nefarious');
  });

  it('should show Login when not logged in', () => {
    mockApiService.isLoggedIn = () => false;
    component.collapseNav();
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.textContent).toContain('Login');
  });

  it('should show username when logged in', () => {
    mockApiService.isLoggedIn = () => true;
    mockApiService.user = { username: 'admin' };
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.textContent).toContain('admin');
  });

  it('should not show Settings link for non-staff', () => {
    mockApiService.user = { is_staff: false };
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.textContent).not.toContain('Settings');
  });

  it('should show Settings link for staff', () => {
    mockApiService.isLoggedIn = () => true;
    mockApiService.user = { username: 'admin', is_staff: true };
    fixture.detectChanges();
    const el = fixture.nativeElement;
    expect(el.textContent).toContain('Settings');
  });

  it('should start with nav collapsed', () => {
    expect(component.isCollapsed).toBeTrue();
  });

  it('should toggle nav collapse', () => {
    component.toggleCollapseNav();
    expect(component.isCollapsed).toBeFalse();
    component.toggleCollapseNav();
    expect(component.isCollapsed).toBeTrue();
  });

  it('should collapse nav on collapseNav call', () => {
    component.isCollapsed = false;
    component.collapseNav();
    expect(component.isCollapsed).toBeTrue();
  });

  it('should return empty username when user is null', () => {
    mockApiService.user = null;
    expect(component.getUserName()).toBe('');
  });

  it('should return username when user exists', () => {
    mockApiService.user = { username: 'auser' };
    expect(component.getUserName()).toBe('auser');
  });
});
