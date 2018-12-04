import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MediaResultsComponent } from './media-results.component';

describe('MediaResultsComponent', () => {
  let component: MediaResultsComponent;
  let fixture: ComponentFixture<MediaResultsComponent>;

  beforeEach(async(() => {
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
