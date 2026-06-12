import { StaffGuard } from './staff.guard';

describe('StaffGuard', () => {
  let mockRouter: jasmine.SpyObj<any>;
  let mockApiService: any;

  beforeEach(() => {
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockApiService = { user: null };
  });

  function createGuard(): StaffGuard {
    const guard = new StaffGuard(mockApiService as any, mockRouter as any);
    return guard;
  }

  it('should create', () => {
    expect(createGuard()).toBeTruthy();
  });

  it('should redirect non-staff users', () => {
    mockApiService.user = { is_staff: false };
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/settings' } as any);
    expect(result).toBeFalse();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should redirect users with no user object', () => {
    mockApiService.user = null;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/settings' } as any);
    expect(result).toBeFalse();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/']);
  });

  it('should allow staff users', () => {
    mockApiService.user = { is_staff: true };
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/settings' } as any);
    expect(result).toBeTrue();
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  });
});
