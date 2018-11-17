import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchAutoComponent } from './search-auto.component';

describe('SearchAutoComponent', () => {
  let component: SearchAutoComponent;
  let fixture: ComponentFixture<SearchAutoComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SearchAutoComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SearchAutoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
