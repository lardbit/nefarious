import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QualityProfilesComponent } from './quality-profiles.component';

describe('QualityProfilesComponent', () => {
  let component: QualityProfilesComponent;
  let fixture: ComponentFixture<QualityProfilesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QualityProfilesComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(QualityProfilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
