import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SearchManualComponent } from './search-manual.component';

describe('SearchManualComponent', () => {
  let component: SearchManualComponent;
  let fixture: ComponentFixture<SearchManualComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SearchManualComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SearchManualComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
