import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RottenTomatoesRedirectComponent } from './rotten-tomatoes-redirect.component';

describe('RottenTomatoesRedirectComponent', () => {
  let component: RottenTomatoesRedirectComponent;
  let fixture: ComponentFixture<RottenTomatoesRedirectComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RottenTomatoesRedirectComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RottenTomatoesRedirectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
