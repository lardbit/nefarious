import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { SearchInputComponent } from './search-input.component';
import { FormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import { StorageMap } from '@ngx-pwa/local-storage';
import { of } from 'rxjs';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';

class MockStorageMap {
  get(_key: string) { return of(null); }
  set(_key: string, _val: any) { return of(undefined); }
}

describe('SearchInputComponent', () => {
  let component: SearchInputComponent;
  let fixture: ComponentFixture<SearchInputComponent>;
  let mockApiService: any;
  let mockToastr: any;
  let mockRoute: any;

  beforeEach(waitForAsync(() => {
    mockApiService = { settings: { preferred_media_category: 'movie' } };
    mockToastr = jasmine.createSpyObj('ToastrService', ['error']);
    mockRoute = { snapshot: { queryParams: {} } };

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [SearchInputComponent],
      providers: [
        { provide: ApiService, useValue: mockApiService },
        { provide: ToastrService, useValue: mockToastr },
        { provide: ActivatedRoute, useValue: mockRoute },
        { provide: StorageMap, useClass: MockStorageMap },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      teardown: { destroyAfterEach: false }
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SearchInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default type to preferred media category', () => {
    expect(component.type).toBe('movie');
  });

  it('should populate q and type from query params', () => {
    mockRoute.snapshot.queryParams = { q: 'Breaking Bad', type: 'tv' };
    component.ngOnInit();
    expect(component.q).toBe('Breaking Bad');
    expect(component.type).toBe('tv');
  });

  it('should emit query on submitSearch', () => {
    component.q = 'The Matrix';
    component.type = 'movie';
    spyOn(component.query, 'emit');
    component.submitSearch();
    expect(component.query.emit).toHaveBeenCalledWith({ q: 'The Matrix', type: 'movie' });
  });

  it('should render radio buttons for movie and tv', () => {
    const el = fixture.nativeElement;
    const movieRadio = el.querySelector('#movie') as HTMLInputElement;
    const tvRadio = el.querySelector('#tv') as HTMLInputElement;
    expect(movieRadio).toBeTruthy();
    expect(tvRadio).toBeTruthy();
  });

  it('should render search input and button', () => {
    const el = fixture.nativeElement;
    expect(el.querySelector('input[name="q"]')).toBeTruthy();
    expect(el.querySelector('button .oi-magnifying-glass')).toBeTruthy();
  });

  it('should disable search button when q is empty', () => {
    component.q = '';
    fixture.detectChanges();
    const el = fixture.nativeElement;
    const btn = el.querySelector('button') as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });
});
