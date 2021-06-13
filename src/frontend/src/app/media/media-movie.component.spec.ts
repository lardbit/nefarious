import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { MediaMovieComponent } from './media-movie.component';

describe('MediaMovieComponent', () => {
  let component: MediaMovieComponent;
  let fixture: ComponentFixture<MediaMovieComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ MediaMovieComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MediaMovieComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
