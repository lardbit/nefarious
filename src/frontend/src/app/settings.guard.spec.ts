import { TestBed, async, inject } from '@angular/core/testing';

import { SettingsGuard } from './settings.guard';

describe('SettingsGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SettingsGuard]
    });
  });

  it('should ...', inject([SettingsGuard], (guard: SettingsGuard) => {
    expect(guard).toBeTruthy();
  }));
});
