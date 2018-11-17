import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchTabsComponent } from './search-tabs.component';

describe('SearchTabsComponent', () => {
  let component: SearchTabsComponent;
  let fixture: ComponentFixture<SearchTabsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SearchTabsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SearchTabsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
