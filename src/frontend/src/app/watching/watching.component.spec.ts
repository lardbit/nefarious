import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { WatchingComponent } from './watching.component';

describe('WatchingComponent', () => {
  let component: WatchingComponent;
  let fixture: ComponentFixture<WatchingComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ WatchingComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WatchingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
