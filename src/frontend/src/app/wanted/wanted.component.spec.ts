import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { WantedComponent } from './wanted.component';

describe('WantedComponent', () => {
  let component: WantedComponent;
  let fixture: ComponentFixture<WantedComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ WantedComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WantedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
