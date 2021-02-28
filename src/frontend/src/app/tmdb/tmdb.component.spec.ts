import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TmdbComponent } from './tmdb.component';

describe('TmdbComponent', () => {
  let component: TmdbComponent;
  let fixture: ComponentFixture<TmdbComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ TmdbComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(TmdbComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
