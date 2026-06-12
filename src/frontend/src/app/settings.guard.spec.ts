import { SettingsGuard } from './settings.guard';

describe('SettingsGuard', () => {
  let mockRouter: jasmine.SpyObj<any>;
  let mockToastr: any;
  let mockApiService: any;

  beforeEach(() => {
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    mockToastr = jasmine.createSpyObj('ToastrService', ['error']);
    mockApiService = {
      settings: null,
      userIsStaff: () => false,
    };
  });

  function createGuard(): SettingsGuard {
    return new SettingsGuard(mockApiService as any, mockRouter as any, mockToastr as any);
  }

  it('should create', () => {
    expect(createGuard()).toBeTruthy();
  });

  it('should allow when jackett token is not the default', () => {
    mockApiService.settings = {
      jackett_token: 'real-token',
      jackett_default_token: 'default-token',
    };
    mockApiService.userIsStaff = () => true;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/search/auto' } as any);
    expect(result).toBeTrue();
  });

  it('should redirect staff to settings when token is default', () => {
    mockApiService.settings = {
      jackett_token: 'default-token',
      jackett_default_token: 'default-token',
    };
    mockApiService.userIsStaff = () => true;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/search/auto' } as any);
    expect(result).toBeFalse();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/settings']);
    expect(mockToastr.error).toHaveBeenCalledWith('missing jackett api token');
  });

  it('should redirect non-staff to page-not-found when token is default', () => {
    mockApiService.settings = {
      jackett_token: 'default-token',
      jackett_default_token: 'default-token',
    };
    mockApiService.userIsStaff = () => false;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/search/auto' } as any);
    expect(result).toBeFalse();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/page-not-found']);
    expect(mockToastr.error).toHaveBeenCalledWith('missing jackett api token - contact admin');
  });

  it('should allow when settings is null (not yet loaded)', () => {
    mockApiService.settings = null;
    const guard = createGuard();
    const result = guard.canActivate({} as any, { url: '/search/auto' } as any);
    expect(result).toBeTrue();
  });
});
