import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { MediaResultsComponent } from './media-results.component';

describe('MediaResultsComponent', () => {
  let component: MediaResultsComponent;
  let fixture: ComponentFixture<MediaResultsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ MediaResultsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MediaResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
