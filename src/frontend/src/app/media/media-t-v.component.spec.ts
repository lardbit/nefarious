import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MediaTVComponent } from './media-t-v.component';

describe('MediaTVComponent', () => {
  let component: MediaTVComponent;
  let fixture: ComponentFixture<MediaTVComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MediaTVComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MediaTVComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
