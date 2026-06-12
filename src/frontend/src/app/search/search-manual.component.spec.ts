import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { SearchManualComponent } from './search-manual.component';
import { ApiService } from '../api.service';
import { ToastrService } from 'ngx-toastr';
import { StorageMap } from '@ngx-pwa/local-storage';
import { MockStorageMap, createMockApiService } from '../test-helpers';

describe('SearchManualComponent', () => {
  let component: SearchManualComponent;
  let fixture: ComponentFixture<SearchManualComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule],
      declarations: [SearchManualComponent],
      providers: [
        { provide: ApiService, useValue: createMockApiService() },
        { provide: ToastrService, useValue: jasmine.createSpyObj('ToastrService', ['success', 'error', 'info']) },
        { provide: StorageMap, useClass: MockStorageMap },
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      teardown: { destroyAfterEach: false }
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SearchManualComponent);
    component = fixture.componentInstance;
    component.tmdbMedia = { name: 'Test Show', title: 'Test Show', poster_image_url: '' };
    component.tmdbTVSeason = { season_number: 1 };
    component.tmdbTVEpisode = { episode_number: 5 };
    component.mediaType = 'tv';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
