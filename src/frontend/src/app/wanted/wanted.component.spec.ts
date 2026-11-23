import { of, throwError } from 'rxjs';
import * as moment from 'moment';

import { WantedComponent } from './wanted.component';

describe('WantedComponent', () => {
  let component: WantedComponent;
  let api: any;
  let toastr: any;

  beforeEach(() => {
    api = {
      SEARCH_MEDIA_TYPE_MOVIE: 'movie',
      SEARCH_MEDIA_TYPE_TV: 'tv',
      watchMovies: [],
      watchTVShows: [],
      watchTVSeasons: [],
      watchTVEpisodes: [],
      mediaUpdated$: of(),
      fetchCurrentTorrents: jasmine.createSpy('fetchCurrentTorrents').and.returnValue(of([])),
      blacklistRetryMovie: jasmine.createSpy('blacklistRetryMovie').and.returnValue(of({})),
      blacklistRetryTVSeason: jasmine.createSpy('blacklistRetryTVSeason').and.returnValue(of({})),
      blacklistRetryTVEpisode: jasmine.createSpy('blacklistRetryTVEpisode').and.returnValue(of({})),
    };
    toastr = { success: jasmine.createSpy('success'), error: jasmine.createSpy('error') };
    const route = { params: of({ type: 'movie' }) };
    const ngZone = { run: (fn: any) => fn() };
    const datePipe = { transform: (v: any) => v };
    const mediaFilter = { transform: (rows: any) => rows };
    component = new WantedComponent(api, toastr, route as any, ngZone as any, datePipe as any, mediaFilter as any);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('statusOf', () => {
    beforeEach(() => {
      component.torrentsLoaded = true;
      component.torrentByMediaId = {};
    });

    it('flags media not released yet', () => {
      const row = { id: 1, release_date: moment().add(10, 'days').format('YYYY-MM-DD') };
      expect(component.statusOf(row).key).toBe('not_released');
    });

    it('flags queued when never attempted', () => {
      const row = { id: 1, release_date: '2000-01-01', last_attempt_date: null };
      expect(component.statusOf(row).key).toBe('queued');
    });

    it('flags no match when attempted but no torrent', () => {
      const row = { id: 1, release_date: '2000-01-01', last_attempt_date: '2020-01-01' };
      expect(component.statusOf(row).key).toBe('no_match');
    });

    it('flags downloading for an active torrent', () => {
      const row = { id: 1, release_date: '2000-01-01', last_attempt_date: '2020-01-01' };
      component.torrentByMediaId = {
        1: { progress: 42, status: 'downloading', date_active: moment().format() },
      };
      expect(component.statusOf(row).key).toBe('downloading');
    });

    it('flags stalled for an idle torrent', () => {
      const row = { id: 1, release_date: '2000-01-01', last_attempt_date: '2020-01-01' };
      component.torrentByMediaId = {
        1: { progress: 42, status: 'idle', date_active: moment().format() },
      };
      expect(component.statusOf(row).key).toBe('stalled');
    });

    it('flags stalled when a downloading torrent has no recent activity', () => {
      const row = { id: 1, release_date: '2000-01-01', last_attempt_date: '2020-01-01' };
      component.torrentByMediaId = {
        1: { progress: 42, status: 'downloading', date_active: moment().subtract(3, 'days').format() },
      };
      expect(component.statusOf(row).key).toBe('stalled');
    });
  });

  describe('canRetry', () => {
    beforeEach(() => {
      component.torrentsLoaded = true;
      component.torrentByMediaId = {};
    });

    it('allows retry for no match', () => {
      expect(component.canRetry({ id: 1, release_date: '2000-01-01', last_attempt_date: '2020-01-01' })).toBe(true);
    });

    it('disallows retry for queued', () => {
      expect(component.canRetry({ id: 1, release_date: '2000-01-01', last_attempt_date: null })).toBe(false);
    });
  });

  describe('retry', () => {
    it('calls the movie retry endpoint and notifies', () => {
      component.mediaType = 'movie';
      component.retry({ id: 5 });
      expect(api.blacklistRetryMovie).toHaveBeenCalledWith(5);
      expect(toastr.success).toHaveBeenCalled();
    });

    it('calls the tv episode retry endpoint', () => {
      component.mediaType = 'tv';
      component.retry({ id: 7, tmdb_episode_id: 99 });
      expect(api.blacklistRetryTVEpisode).toHaveBeenCalledWith(7);
    });

    it('calls the tv season retry endpoint', () => {
      component.mediaType = 'tv';
      component.retry({ id: 8 });
      expect(api.blacklistRetryTVSeason).toHaveBeenCalledWith(8);
    });

    it('notifies on error', () => {
      api.blacklistRetryMovie.and.returnValue(throwError('boom'));
      component.mediaType = 'movie';
      component.retry({ id: 5 });
      expect(toastr.error).toHaveBeenCalled();
      expect(component.retrying[5]).toBe(false);
    });
  });
});
