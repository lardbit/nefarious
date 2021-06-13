import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { TorrentDetailsComponent } from './torrent-details.component';

describe('TorrentDetailsComponent', () => {
  let component: TorrentDetailsComponent;
  let fixture: ComponentFixture<TorrentDetailsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ TorrentDetailsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TorrentDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
