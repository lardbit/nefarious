import { TestBed, inject, waitForAsync } from '@angular/core/testing';

import { StaffGuard } from './staff.guard';

describe('StaffGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
    providers: [StaffGuard],
    teardown: { destroyAfterEach: false }
});
  });

  it('should ...', inject([StaffGuard], (guard: StaffGuard) => {
    expect(guard).toBeTruthy();
  }));
});
