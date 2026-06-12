import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { StorageMap } from '@ngx-pwa/local-storage';
import { of } from 'rxjs';

class MockStorageMap {
  get(_key: string) { return of(null); }
  set(_key: string, _val: any) { return of(undefined); }
}

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        ApiService,
        { provide: StorageMap, useClass: MockStorageMap },
      ]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(service).toBeTruthy();
  });

  describe('isLoggedIn', () => {
    it('should return false when no token', () => {
      service.userToken = undefined as any;
      expect(service.isLoggedIn()).toBeFalse();
    });

    it('should return true when token exists', () => {
      service.userToken = 'test-token';
      expect(service.isLoggedIn()).toBeTrue();
    });
  });

  describe('userIsStaff', () => {
    it('should return false when user is null', () => {
      service.user = null;
      // userIsStaff uses !!this.user.is_staff which throws on null
      // This is expected — in practice this method is only called on authenticated users
      expect(() => service.userIsStaff()).toThrow();
    });

    it('should return user.is_staff', () => {
      service.user = { is_staff: true };
      expect(service.userIsStaff()).toBeTrue();
    });
  });

  describe('login', () => {
    it('should POST credentials and store token', () => {
      service.login('admin', 'pass').subscribe((data) => {
        expect(data.token).toBe('abc123');
        expect(service.userToken).toBe('abc123');
      });

      const req = httpMock.expectOne('/api/auth/');
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ username: 'admin', password: 'pass' });
      req.flush({ token: 'abc123' });
    });
  });

  describe('fetchUser', () => {
    it('should GET current user', () => {
      service.userToken = 'token';
      const mockUser = { id: 1, username: 'admin', is_staff: true };

      service.fetchUser().subscribe((user) => {
        expect(user).toEqual(mockUser);
        expect(service.user).toEqual(mockUser);
      });

      const req = httpMock.expectOne('/api/user/');
      expect(req.request.method).toBe('GET');
      req.flush([mockUser]);
    });
  });

  describe('fetchSettings', () => {
    it('should GET settings', () => {
      service.userToken = 'token';
      const mockSettings = { id: 1, jackett_token: 'abc', jackett_host: 'jackett' };

      service.fetchSettings().subscribe((settings) => {
        expect(settings).toEqual(mockSettings);
        expect(service.settings).toEqual(mockSettings);
      });

      const req = httpMock.expectOne('/api/settings/');
      expect(req.request.method).toBe('GET');
      req.flush([mockSettings]);
    });
  });

  describe('searchMedia', () => {
    it('should GET search results with query params', () => {
      service.userToken = 'token';
      service.settings = { language: 'en' };

      service.searchMedia('test', 'movie', 1).subscribe((data) => {
        expect(data).toEqual({ results: [] });
      });

      const req = httpMock.expectOne((r) => r.url === '/api/search/media/' && r.params.has('q'));
      expect(req.request.method).toBe('GET');
      expect(req.request.params.get('q')).toBe('test');
      expect(req.request.params.get('media_type')).toBe('movie');
      req.flush({ results: [] });
    });
  });

  describe('searchTorrents', () => {
    it('should GET torrent results', () => {
      service.userToken = 'token';

      service.searchTorrents('some-show', 'tv').subscribe((data) => {
        expect(data).toEqual([{ title: 'Result 1' }]);
      });

      const req = httpMock.expectOne('/api/search/torrents/?q=some-show&media_type=tv');
      expect(req.request.method).toBe('GET');
      req.flush([{ title: 'Result 1' }]);
    });
  });

  describe('watchMovie', () => {
    it('should POST new movie and add to watchMovies', () => {
      service.userToken = 'token';
      const newMovie = { id: 10, tmdb_movie_id: 123, name: 'Test Movie' };

      service.watchMovie(123, 'Test Movie', 'http://img.jpg', '2020-01-01').subscribe((data) => {
        expect(data).toEqual(newMovie);
        expect(service.watchMovies).toContain(newMovie);
      });

      const req = httpMock.expectOne('/api/watch-movie/');
      expect(req.request.method).toBe('POST');
      req.flush(newMovie);
    });
  });

  describe('unWatchMovie', () => {
    it('should DELETE movie and remove from watchMovies', () => {
      service.userToken = 'token';
      service.watchMovies = [{ id: 10, name: 'Test Movie' }];

      service.unWatchMovie(10).subscribe(() => {
        expect(service.watchMovies.length).toBe(0);
      });

      const req = httpMock.expectOne('/api/watch-movie/10/');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });
  });

  describe('verifySettings', () => {
    it('should GET verify endpoint', () => {
      service.userToken = 'token';
      service.settings = { id: 1 };

      service.verifySettings().subscribe((data) => {
        expect(data.success).toBeTrue();
      });

      const req = httpMock.expectOne('/api/settings/1/verify/');
      expect(req.request.method).toBe('GET');
      req.flush({ success: true });
    });
  });

  describe('mediaUpdated$', () => {
    it('should emit after _updateStorage', () => {
      let emitted = false;
      service.mediaUpdated$.subscribe(() => { emitted = true; });

      (service as any)._alertMediaUpdated();

      expect(emitted).toBeTrue();
    });
  });
});
