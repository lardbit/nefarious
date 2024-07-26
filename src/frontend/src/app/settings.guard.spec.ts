import { TestBed, inject, waitForAsync } from '@angular/core/testing';

import { SettingsGuard } from './settings.guard';

describe('SettingsGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
    providers: [SettingsGuard],
    teardown: { destroyAfterEach: false }
});
  });

  it('should ...', inject([SettingsGuard], (guard: SettingsGuard) => {
    expect(guard).toBeTruthy();
  }));
});
