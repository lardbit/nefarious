import { LoginGuard } from './login.guard';

describe('LoginGuard', () => {
  let mockRouter: jasmine.SpyObj<any>;
  let mockApiService: any;

  beforeEach(() => {
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockApiService = { isLoggedIn: () => false };
  });

  function createGuard(): LoginGuard {
    return new LoginGuard(mockApiService as any, mockRouter as any);
  }

  it('should create', () => {
    expect(createGuard()).toBeTruthy();
  });

  it('should redirect when not logged in', () => {
    mockApiService.isLoggedIn = () => false;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/search/auto' } as any);
    expect(result).toBeFalse();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should allow when logged in', () => {
    mockApiService.isLoggedIn = () => true;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/search/auto' } as any);
    expect(result).toBeTrue();
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  });
});
