import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RottenTomatoesComponent } from './rotten-tomatoes.component';

describe('RottenTomatoesComponent', () => {
  let component: RottenTomatoesComponent;
  let fixture: ComponentFixture<RottenTomatoesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ RottenTomatoesComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(RottenTomatoesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
