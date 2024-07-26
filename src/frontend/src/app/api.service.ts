import { StorageMap } from '@ngx-pwa/local-storage';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, mergeMap, tap } from 'rxjs/operators';
import { forkJoin, Observable, of, Subject, zip } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';


@Injectable({
  providedIn: 'root'
})
export class ApiService {
  STORAGE_KEY_API_TOKEN = 'NEFARIOUS-API-TOKEN';
  STORAGE_KEY_USER = 'NEFARIOUS-USER';
  STORAGE_KEY_WATCH_MOVIES = 'NEFARIOUS-WATCH_MOVIES';
  STORAGE_KEY_WATCH_TV_SHOWS = 'NEFARIOUS-WATCH_TV_SHOWS';
  STORAGE_KEY_WATCH_TV_SEASONS = 'NEFARIOUS-WATCH_TV_SEASONS';
  STORAGE_KEY_WATCH_TV_SEASON_REQUESTS = 'NEFARIOUS-WATCH_TV_SEASON_REQUESTS';
  STORAGE_KEY_WATCH_TV_EPISODES = 'NEFARIOUS-WATCH_TV_EPISODES';

  API_URL_USER = '/api/user/';
  API_URL_USERS = '/api/users/';
  API_URL_LOGIN = '/api/auth/';
  API_URL_SETTINGS = '/api/settings/';
  API_URL_SEARCH_TORRENTS = '/api/search/torrents/';
  API_URL_DOWNLOAD_TORRENTS = '/api/download/torrents/';
  API_URL_SEARCH_MEDIA = '/api/search/media/';
  API_URL_SEARCH_SIMILAR_MEDIA = '/api/search/similar/media/';
  API_URL_SEARCH_RECOMMENDED_MEDIA = '/api/search/recommended/media/';
  API_URL_WATCH_TV_EPISODE = '/api/watch-tv-episode/';
  API_URL_WATCH_TV_SHOW = '/api/watch-tv-show/';
  API_URL_WATCH_TV_SEASON = '/api/watch-tv-season/';
  API_URL_WATCH_TV_SEASON_REQUEST = '/api/watch-tv-season-request/';
  API_URL_WATCH_MOVIE = '/api/watch-movie/';
  API_URL_CURRENT_TORRENTS = '/api/current/torrents/';
  API_URL_DISCOVER_MOVIES = '/api/discover/media/movie/';
  API_URL_DISCOVER_TV = '/api/discover/media/tv/';
  API_URL_DISCOVER_RT_MOVIES = '/api/discover/rotten-tomatoes/media/movie/';
  API_URL_GENRES_MOVIE = '/api/genres/movie/';
  API_URL_GENRES_TV = '/api/genres/tv/';
  API_URL_MEDIA_CATEGORIES = '/api/media-categories/';
  API_URL_QUALITY_PROFILES = '/api/quality-profiles/';
  API_URL_GIT_COMMIT = '/api/git-commit/';
  API_URL_IMPORT_MEDIA_TV = '/api/import/media/tv/';
  API_URL_IMPORT_MEDIA_MOVIE = '/api/import/media/movie/';
  API_URL_OPEN_SUBTITLES_AUTH = '/api/open-subtitles/auth/';
  API_URL_QUEUE_TASK = '/api/queue-task/';
  API_URL_SEND_TEST_NOTIFICATION = '/api/notifications/';
  API_URL_BLACKLISTS_DELETE = '/api/torrent-blacklist/delete-all/';

  SEARCH_MEDIA_TYPE_TV = 'tv';
  SEARCH_MEDIA_TYPE_MOVIE = 'movie';

  public user: any;
  public userToken: string;
  public users: any; // staff-only list of all users
  public settings: any;
  public qualityProfiles: string[];
  public mediaCategories: string[];
  public watchTVSeasons: any[] = [];
  public watchTVSeasonRequests: any[] = [];
  public watchTVEpisodes: any[] = [];
  public watchTVShows: any[] = [];
  public watchMovies: any[] = [];

  public mediaUpdated$ = new Subject<any>();

  protected _webSocket: WebSocketSubject<any>;


  constructor(
    private http: HttpClient,
    private localStorage: StorageMap,
  ) {
  }

  public init(): Observable<any> {

    return this.loadFromStorage().pipe(
      mergeMap((data) => {
        if (this.user) {
          console.log('logged in with token: %s, fetching user', this.userToken);
          return this.fetchUser().pipe(
            mergeMap(() => {
              console.log('fetching core data');
              return this.fetchCoreData().pipe(
                tap(() => {
                  // fetch watch media in the background since we loaded from storage already
                  this.fetchWatchMedia().subscribe();
                })
              );
            }),
            catchError((error) => {
              // unauthorized response, remove existing user and token
              if (error.status === 401) {
                console.log('Unauthorized - removing user & token');
                delete this.userToken;
                delete this.user;
              }
              return of(error);
            })
          );
        } else {
          console.log('not logged in');
          return of(null);
        }
      }),
    );
  }

  public userIsStaff(): boolean {
    return !!this.user.is_staff;
  }

  public loadFromStorage(): Observable<any> {
    return zip(
      this.localStorage.get(this.STORAGE_KEY_API_TOKEN).pipe(
        map(
          (data: string) => {
            this.userToken = data;
            return this.userToken;
          }),
      ),
      this.localStorage.get(this.STORAGE_KEY_USER).pipe(
        map(
          (data) => {
            this.user = data;
            return this.user;
          }),
      ),
      this.localStorage.get(this.STORAGE_KEY_WATCH_MOVIES).pipe(
        map(
          (data: any[]) => {
            this.watchMovies = data || [];
            return this.watchMovies;
          }),
      ),
      this.localStorage.get(this.STORAGE_KEY_WATCH_TV_SHOWS).pipe(
        map(
          (data: any[]) => {
            this.watchTVShows = data || [];
            return this.watchTVShows;
          }),
      ),
      this.localStorage.get(this.STORAGE_KEY_WATCH_TV_SEASONS).pipe(
        map(
          (data: any[]) => {
            this.watchTVSeasons = data || [];
            return this.watchTVSeasons;
          }),
      ),
      this.localStorage.get(this.STORAGE_KEY_WATCH_TV_SEASON_REQUESTS).pipe(
        map(
          (data: any[]) => {
            this.watchTVSeasonRequests = data || [];
            return this.watchTVSeasonRequests;
          }),
      ),
      this.localStorage.get(this.STORAGE_KEY_WATCH_TV_EPISODES).pipe(
        map(
          (data: any[]) => {
            this.watchTVEpisodes = data || [];
            return this.watchTVEpisodes;
          }),
      ),
    );
  }

  public isLoggedIn(): boolean {
    return !!this.userToken;
  }

  public fetchCoreData(): Observable<any> {
    return forkJoin([
      this.fetchSettings().pipe(
        tap(() => {
          // only initialize when in production
          if (!this.settings.is_debug) {
            this._initWebSocket();
          }
        })
      ),
      this.fetchQualityProfiles(),
      this.fetchMediaCategories(),
    ]).pipe(
      catchError((error) => {
        console.error(error);
        return of(error);
      })
    );
  }

  public fetchWatchMedia(afterDateUpdated?: string): Observable<any> {
    let params: any = {};

    // conditionally include an "updated after date" parameter
    if (afterDateUpdated) {
      params.date_updated__gte = afterDateUpdated;
    }

    return forkJoin([
      this.fetchWatchTVShows(),  // "shows" don't support the "after date updated" parameter
      this.fetchWatchTVSeasons(params),
      this.fetchWatchTVSeasonRequests(params),
      this.fetchWatchTVEpisodes(params),
      this.fetchWatchMovies(params),
    ]).pipe(
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public fetchSettings() {
    return this.http.get(this.API_URL_SETTINGS, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        if (data.length) {
          this.settings = data[0];
        } else {
          console.log('no settings');
        }
        return this.settings;
      }),
    );
  }

  public fetchMediaCategories() {
    return this.http.get(this.API_URL_MEDIA_CATEGORIES, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        if (data.mediaCategories) {
          this.mediaCategories = data.mediaCategories;
        } else {
          console.error('no media categories');
        }
        return this.mediaCategories;
      }),
    );
  }

  public fetchQualityProfiles() {
    return this.http.get(this.API_URL_QUALITY_PROFILES, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        if (data.profiles) {
          this.qualityProfiles = data.profiles;
        } else {
          console.error('no quality profiles');
        }
        return this.qualityProfiles;
      }),
    );
  }

  public fetchUser(): Observable<any> {
    // fetches current user
    return this.http.get(this.API_URL_USER, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        if (data.length) {
          this.user = data[0];
          this.localStorage.set(this.STORAGE_KEY_USER, this.user).subscribe();
          return this.user;
        } else {
          console.log('no user');
          return null;
        }
      }),
    );
  }

  public updateUser(id: number, params: any): Observable<any> {
    return this.http.put(`${this.API_URL_USERS}${id}/`, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public createUser(username: string, password: string): Observable<any> {
    const params = {username: username, password: password};
    return this.http.post(this.API_URL_USERS, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.users.push(data);
        return data;
      }),
    );
  }

  public deleteUser(id: number): Observable<any> {
    return this.http.delete(`${this.API_URL_USERS}${id}/`, {headers: this._requestHeaders()}).pipe(
      tap((data: any) => {
        this.users.filter((user) => {
          return user.id !== id;
        });
      }),
    );
  }

  public fetchUsers(): Observable<any> {
    return this.http.get(this.API_URL_USERS, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.users = data;
        return this.users;
      }),
    );
  }

  public login(user: string, pass: string) {
    const params = {
      username: user,
      password: pass,
    };
    return this.http.post(this.API_URL_LOGIN, params).pipe(
      map((data: any) => {
        console.log('token auth', data);
        this.userToken = data.token;
        this.localStorage.set(this.STORAGE_KEY_API_TOKEN, this.userToken).subscribe(
          (wasSet) => {
            console.log('local storage set', wasSet);
          },
          (error) => {
            console.error('local storage error', error);
          }
        );
        return data;
      }),
    );
  }

  public updateSettings(id: number, params: any) {
    return this.http.patch(`${this.API_URL_SETTINGS}${id}/`, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.settings = data;
        return this.settings;
      }),
    );
  }

  public searchTorrents(query: string, mediaType: string) {
    return this.http.get(`${this.API_URL_SEARCH_TORRENTS}?q=${query}&media_type=${mediaType}`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public download(torrentResult: any, mediaType: string, tmdbMedia: any, params?: any) {
    // add extra params
    Object.assign(params || {}, {
      torrent: torrentResult,
      media_type: mediaType,
      tmdb_media: tmdbMedia,
    });
    return this.http.post(this.API_URL_DOWNLOAD_TORRENTS, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        if (data.success) {
          if (mediaType === this.SEARCH_MEDIA_TYPE_MOVIE) {
            this.watchMovies.push(data.watch_movie);
          } else if (mediaType === this.SEARCH_MEDIA_TYPE_TV) {
            // add show if it wasn't being watched already
            const watchShow = this.watchTVShows.find((show) => {
              return show.id === data.watch_show;
            });
            if (!watchShow) {
              this.watchTVShows.push(data.watch_tv_show);
            }

            // add tv season request or episode to existing lists
            if (data.watch_tv_season_request) {
              this.watchTVSeasonRequests.push(data.watch_tv_season_request);
            } else if (data.watch_tv_episode) {
              this.watchTVEpisodes.push(data.watch_tv_episode);
            }
          }
          this._updateStorage().subscribe();
        }
        return data;
      }),
    );
  }

  public searchMedia(query: string, mediaType: string, page = 1) {
    let params = {
      q: query,
      media_type: mediaType,
      page: page.toString(),
    };
    params = Object.assign(params, this._defaultParams());
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_SEARCH_MEDIA, {headers: this._requestHeaders(), params: httpParams}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public searchSimilarMedia(tmdbMediaId: string, mediaType: string) {
    let params = {
      tmdb_media_id: tmdbMediaId,
      media_type: mediaType,
    };
    params = Object.assign(params, this._defaultParams());
    const httpParams = new HttpParams({fromObject: params});
    const options = {headers: this._requestHeaders(), params: httpParams};
    return this.http.get(this.API_URL_SEARCH_SIMILAR_MEDIA, options).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public searchRecommendedMedia(tmdbMediaId: string, mediaType: string) {
    let params = {
      tmdb_media_id: tmdbMediaId,
      media_type: mediaType,
    };
    params = Object.assign(params, this._defaultParams());
    const httpParams = new HttpParams({fromObject: params});
    const options = {headers: this._requestHeaders(), params: httpParams};
    return this.http.get(this.API_URL_SEARCH_RECOMMENDED_MEDIA, options).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public searchMediaDetail(mediaType: string, id: string) {
    const options = {headers: this._requestHeaders(), params: this._defaultParams()};
    return this.http.get(`${this.API_URL_SEARCH_MEDIA}${mediaType}/${id}/`, options).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public fetchMediaVideos(mediaType: string, id: string) {
    const options = {headers: this._requestHeaders()};
    return this.http.get(`${this.API_URL_SEARCH_MEDIA}${mediaType}/${id}/videos/`, options).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public fetchWatchTVShows(params?: any) {
    params = params || {};
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_WATCH_TV_SHOW, {params: httpParams, headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchTVShows = data;
        return this.watchTVShows;
      }),
    );
  }

  public fetchWatchTVSeasons(params?: any) {
    params = params || {};
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_WATCH_TV_SEASON, {params: httpParams, headers: this._requestHeaders()}).pipe(
      map((records: any) => {
        // if filter params are present we should merge the results
        if (httpParams.keys().length > 0) {
          this._mergeMediaRecords(this.watchTVSeasons, records);
        } else {
          this.watchTVSeasons = records;
        }
        return this.watchTVSeasons;
      }),
    );
  }

  public fetchWatchTVSeasonRequests(params?: any) {
    params = params || {};
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_WATCH_TV_SEASON_REQUEST, {params: httpParams, headers: this._requestHeaders()}).pipe(
      map((records: any) => {
        // if filter params are present we should merge the results
        if (httpParams.keys().length > 0) {
          this._mergeMediaRecords(this.watchTVSeasonRequests, records);
        } else {
          this.watchTVSeasonRequests = records;
        }
        return this.watchTVSeasonRequests;
      }),
    );
  }

  public fetchWatchMovies(params?: any) {
    params = params || {};
    const httpParams = new HttpParams({fromObject: params});

    return this.http.get(this.API_URL_WATCH_MOVIE, {params: httpParams, headers: this._requestHeaders()}).pipe(
      map((records: any[]) => {
        // if filter params are present we should merge the results
        if (httpParams.keys().length > 0) {
          this._mergeMediaRecords(this.watchMovies, records);
        } else {
          this.watchMovies = records;
        }
        return this.watchMovies;
      }),
    );
  }

  public fetchWatchTVEpisodes(params: any) {
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_WATCH_TV_EPISODE, {headers: this._requestHeaders(), params: httpParams}).pipe(
      map((records: any) => {
        // if filter params are present we should merge the results
        if (httpParams.keys().length > 0) {
          this._mergeMediaRecords(this.watchTVEpisodes, records);
        } else {
          this.watchTVEpisodes = records;
        }
        return this.watchTVEpisodes;
      }),
    );
  }

  public fetchCurrentTorrents(params: any) {
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_CURRENT_TORRENTS, {headers: this._requestHeaders(), params: httpParams}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public watchTVShow(
    showId: number, name: string, posterImageUrl: string,
    releaseDate: string, autoWatchNewSeasons?: boolean, qualityProfile?: string) {
    const params = {
      tmdb_show_id: showId,
      name: name,
      poster_image_url: posterImageUrl,
      release_date: releaseDate || null,
      auto_watch: !!autoWatchNewSeasons,
      quality_profile_custom: qualityProfile,
    };
    return this.http.post(this.API_URL_WATCH_TV_SHOW, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const found = this.watchTVShows.find((media) => {
          return media.id === data['id'];
        });
        if (!found) {
          this.watchTVShows.push(data);
        }
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public updateWatchTVShow(id: number, params: any) {
    return this.http.patch(`${this.API_URL_WATCH_TV_SHOW}${id}/`, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const showIndex = this.watchTVShows.findIndex((media) => {
          return media.id === data['id'];
        });
        if (showIndex >= 0) {
          // update show
          Object.assign(this.watchTVShows[showIndex], data);
        }
        return this.watchTVShows[showIndex];
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public watchTVEpisode(watchShowId: number, episodeId: number, seasonNumber: number, episodeNumber: number, releaseDate: string) {
    const params = {
      watch_tv_show: watchShowId,
      tmdb_episode_id: episodeId,
      season_number: seasonNumber,
      episode_number: episodeNumber,
      release_date: releaseDate || null,
    };
    return this.http.post(this.API_URL_WATCH_TV_EPISODE, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const found = this.watchTVEpisodes.find((media) => {
          return media.id === data['id'];
        });
        if (!found) {
          this.watchTVEpisodes.push(data);
        }
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public watchTVSeasonRequest(watchShowId: number, seasonNumber: number, releaseDate: string) {
    const params = {
      watch_tv_show: watchShowId,
      season_number: seasonNumber,
      release_date: releaseDate || null,
    };
    return this.http.post(this.API_URL_WATCH_TV_SEASON_REQUEST, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const found = this.watchTVSeasonRequests.find((media) => {
          return media.id === data['id'];
        });
        if (!found) {
          this.watchTVSeasonRequests.push(data);
        }
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public unWatchTVShow(watchId) {
    return this.http.delete(`${this.API_URL_WATCH_TV_SHOW}${watchId}/`, {headers: this._requestHeaders()}).pipe(
      tap((data: any) => {
        // filter out records
        this.watchTVShows = this.watchTVShows.filter((watch) => {
          return watch.id !== watchId;
        });
        this.watchTVSeasons = this.watchTVSeasons.filter((watch) => {
          return watch.watch_tv_show !== watchId;
        });
        this.watchTVSeasonRequests = this.watchTVSeasonRequests.filter((watch) => {
          return watch.watch_tv_show !== watchId;
        });
        this.watchTVEpisodes = this.watchTVEpisodes.filter((watch) => {
          return watch.watch_tv_show !== watchId;
        });
        this._updateStorage().subscribe();
      })
    );
  }

  public unWatchTVEpisode(watchId) {
    return this.http.delete(`${this.API_URL_WATCH_TV_EPISODE}${watchId}/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const foundIndex = this.watchTVEpisodes.findIndex((watch) => {
          return watch.id === watchId;
        });
        if (foundIndex >= 0) {
          this.watchTVEpisodes.splice(foundIndex, 1);
        }
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public watchMovie(movieId: number, name: string, posterImageUrl: string, releaseDate: string, qualityProfileCustom?: string) {
    const params = {
      tmdb_movie_id: movieId,
      name: name,
      poster_image_url: posterImageUrl,
      quality_profile_custom: qualityProfileCustom,
      release_date: releaseDate || null,
    };

    return this.http.post(this.API_URL_WATCH_MOVIE, params, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const found = this.watchMovies.find((media) => {
          return media.id === data['id'];
        });
        if (!found) {
          this.watchMovies.push(data);
        }
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public unWatchMovie(watchId) {
    return this.http.delete(`${this.API_URL_WATCH_MOVIE}${watchId}/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const foundIndex = this.watchMovies.findIndex((watch) => {
          return watch.id === watchId;
        });
        if (foundIndex >= 0) {
          this.watchMovies.splice(foundIndex, 1);
        }
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public unWatchTVSeason(watchTVSeasonRequestId) {
    // NOTE: expects a "tv season request"

    return this.http.delete(`${this.API_URL_WATCH_TV_SEASON_REQUEST}${watchTVSeasonRequestId}/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {

        // find the season request instance
        const foundWatchRequestIndex = this.watchTVSeasonRequests.findIndex((watch) => {
          return watch.id === watchTVSeasonRequestId;
        });
        if (foundWatchRequestIndex === -1) {
          return;
        }

        // remove the season request
        const foundWatchRequest = this.watchTVSeasonRequests[foundWatchRequestIndex];
        this.watchTVSeasonRequests.splice(foundWatchRequestIndex, 1);

        // find and remove the watch seasons
        const foundWatchIndex = this.watchTVSeasons.findIndex((watch) => {
          return foundWatchRequest.tmdb_show_id === watch.tmdb_show_id && foundWatchRequest.season_number === watch.season_number;
        });
        if (foundWatchIndex >= 0) {
          this.watchTVSeasons.splice(foundWatchIndex, 1);
        }

        // find and remove individual episodes
        this.watchTVEpisodes = this.watchTVEpisodes.filter((watch) => {
          return watch.watch_tv_show !== foundWatchRequest.watch_tv_show;
        });

        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public verifySettings() {
    return this.http.get(`${this.API_URL_SETTINGS}${this.settings.id}/verify/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public blacklistRetryMovie(watchMediaId: number) {
    return this.http.post(`${this.API_URL_WATCH_MOVIE}${watchMediaId}/blacklist-auto-retry/`, null, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchMovies.forEach((watchMovie) => {
          if (data.id === watchMovie.id) {
            Object.assign(watchMovie, data);
          }
        });
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public blacklistRetryTVSeason(watchMediaId: number) {
    const url = `${this.API_URL_WATCH_TV_SEASON}${watchMediaId}/blacklist-auto-retry/`;
    const options = {headers: this._requestHeaders()};
    return this.http.post(url, null, options).pipe(
      map((data: any) => {
        this.watchTVSeasons.forEach((watchSeason) => {
          if (data.id === watchSeason.id) {
            Object.assign(watchSeason, data);
          }
        });
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public blacklistRetryTVEpisode(watchMediaId: number) {
    const url = `${this.API_URL_WATCH_TV_EPISODE}${watchMediaId}/blacklist-auto-retry/`;
    return this.http.post(url, null, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchTVEpisodes.forEach((watchEpisode) => {
          if (data.id === watchEpisode.id) {
            Object.assign(watchEpisode, data);
          }
        });
        return data;
      }),
      tap(() => {
        this._updateStorage().subscribe();
      }),
    );
  }

  public discoverMovies(params: any) {
    return this._discoverMedia(this.SEARCH_MEDIA_TYPE_MOVIE, params);
  }

  public discoverTV(params: any) {
    return this._discoverMedia(this.SEARCH_MEDIA_TYPE_TV, params);
  }

  public fetchMovieGenres() {
    return this._fetchGenres(this.SEARCH_MEDIA_TYPE_MOVIE);
  }

  public fetchTVGenres() {
    return this._fetchGenres(this.SEARCH_MEDIA_TYPE_TV);
  }

  public verifyJackettIndexers() {
    return this.http.get(`${this.API_URL_SETTINGS}${this.settings.id}/verify-jackett-indexers/`, {headers: this._requestHeaders()});
  }

  public fetchGitCommit(): Observable<any> {
    return this.http.get(this.API_URL_GIT_COMMIT, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public importMedia(mediaType: string): Observable<any> {
    const url = mediaType === this.SEARCH_MEDIA_TYPE_MOVIE ? this.API_URL_IMPORT_MEDIA_MOVIE : this.API_URL_IMPORT_MEDIA_TV;
    return this.http.post(url, null, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        return data;
      }),
    );
  }

  public discoverRottenTomatoesMedia(mediaType: string, params: any) {
    params = Object.assign(params, this._defaultParams());
    const httpParams = new HttpParams({fromObject: params});
    const url = this.API_URL_DISCOVER_RT_MOVIES;
    return this.http.get(url, {params: httpParams, headers: this._requestHeaders()});
  }

  public openSubtitlesAuth() {
    const url = this.API_URL_OPEN_SUBTITLES_AUTH;
    return this.http.post(url, null, {headers: this._requestHeaders()});
  }

  public queueTask(task: string) {
    const params = { task: task };
    const url = this.API_URL_QUEUE_TASK;
    return this.http.post(url, params, {headers: this._requestHeaders()});
  }

  public sendNotification(message: string): Observable<any> {
    return this.http.post(this.API_URL_SEND_TEST_NOTIFICATION, {message}, {headers: this._requestHeaders()});
  }

  public deleteAllBlacklists(): Observable<any> {
    return this.http.post(this.API_URL_BLACKLISTS_DELETE, null, {headers: this._requestHeaders()});
  }

  protected _mergeMediaRecords(existingRecords: any[], updatedRecords: any[]) {
    // merge new/updated media records
    updatedRecords.forEach((updatedRecord) => {
      // find matching record
      const mediaIndex = existingRecords.findIndex((media) => {
        return media.id === updatedRecord.id;
      });
      // found - update existing value
      if (mediaIndex >= 0) {
        existingRecords[mediaIndex] = updatedRecord;
      } else {
        existingRecords.push(updatedRecord);
      }
    })
  }

  protected _initWebSocket() {

    // we can't rely on the server's websocket url because it may be "nefarious" when run in a docker stack,
    // so we'll just extract the port and path and use the current window's url
    const serverWebSocketURL = new URL(this.settings.websocket_url);
    const windowLocation = window.location;
    const webSocketProtocol = `${windowLocation.protocol === 'https:' ? 'wss' : 'ws'}://`;
    const webSocketHost = `${webSocketProtocol}${windowLocation.hostname}:${windowLocation.port}${serverWebSocketURL.pathname}`;

    console.log('Connecting to WebSocket URL: %s', webSocketHost);

    this._webSocket = webSocket(webSocketHost);

    this._webSocket.subscribe(
      (data) => {
        this._handleWebSocketMessage(data);
      },
      () => {
        console.error('websocket error. reconnecting...');
        this._reconnectWebSocket();
      },
      () => {
        console.warn('websocket closed. reconnecting...');
        this._reconnectWebSocket();
      }
    );
  }

  protected _reconnectWebSocket() {
    if (this._webSocket && !this._webSocket.closed) {
      console.warn('reinitializing websocket');
      this._webSocket.unsubscribe();
    } else {
      console.log('initializing websocket');
    }
    setTimeout(() => {
      this._initWebSocket();
    }, 500);
  }

  protected _handleWebSocketMessage(data: string) {
    try {
      data = JSON.parse(data);
    } catch (err) {
      console.error('websocket message not json', err);
      return;
    }

    let mediaList = [];

    if (data['type'] === 'MOVIE') {
      mediaList = this.watchMovies;
    } else if (data['type'] === 'TV_SHOW') {
      mediaList = this.watchTVShows;
    } else if (data['type'] === 'TV_SEASON') {
      mediaList = this.watchTVSeasons;
    } else if (data['type'] === 'TV_SEASON_REQUEST') {
      mediaList = this.watchTVSeasonRequests;
    } else if (data['type'] === 'TV_EPISODE') {
      mediaList = this.watchTVEpisodes;
    } else {
      console.error('Unknown websocket message', data);
      return;
    }

    // find existing media and update it or add to appropriate media list
    const watchMediaIndex = mediaList.findIndex((media) => {
      return media.id === data['data'].id;
    });
    if (data['action'] === 'UPDATED') {
      // update existing media
      if (watchMediaIndex >= 0) {
        Object.assign(mediaList[watchMediaIndex], data['data']);
      } else {
        // add to media list
        mediaList.push(data['data']);
      }
    } else if (data['action'] === 'REMOVED') {
      // remove media
      if (watchMediaIndex >= 0) {
        mediaList.splice(watchMediaIndex, 1);
      } else {
        console.warn('could not find media to remove', data['data']);
      }
    }

    this._updateStorage().subscribe();
  }

  protected _fetchGenres(mediaType: string) {
    const url = mediaType === this.SEARCH_MEDIA_TYPE_MOVIE ? this.API_URL_GENRES_MOVIE : this.API_URL_GENRES_TV;
    const params = this._defaultParams();
    return this.http.get(url, {headers: this._requestHeaders(), params: params});
  }

  protected _discoverMedia(mediaType: string, params: any) {
    params = Object.assign(params, this._defaultParams());
    const httpParams = new HttpParams({fromObject: params});
    const url = mediaType === this.SEARCH_MEDIA_TYPE_MOVIE ? this.API_URL_DISCOVER_MOVIES : this.API_URL_DISCOVER_TV;
    return this.http.get(url, {params: httpParams, headers: this._requestHeaders()});
  }

  protected _defaultParams() {
    // include "language" to effectively cache-bust when they change their language setting
    return {
      'language': this.settings.language,
    };
  }

  protected _requestHeaders() {
    return new HttpHeaders({
      'Content-Type':  'application/json',
      'Authorization': `Token ${this.userToken}`,
    });
  }

  protected _updateStorage(): Observable<any> {

    // sort media
    this.watchMovies.sort(this._sortWatchMediaByName);
    this.watchTVShows.sort(this._sortWatchMediaByName);

    // set in storage
    return forkJoin([
      this.localStorage.set(this.STORAGE_KEY_WATCH_MOVIES, this.watchMovies),
      this.localStorage.set(this.STORAGE_KEY_WATCH_TV_SHOWS, this.watchTVShows),
      this.localStorage.set(this.STORAGE_KEY_WATCH_TV_SEASONS, this.watchTVSeasons),
      this.localStorage.set(this.STORAGE_KEY_WATCH_TV_SEASON_REQUESTS, this.watchTVSeasonRequests),
      this.localStorage.set(this.STORAGE_KEY_WATCH_TV_EPISODES, this.watchTVEpisodes),
    ]).pipe(
      tap(() => {
        // send event updates
        this._alertMediaUpdated();
      })
    );
  }

  protected _alertMediaUpdated() {
    this.mediaUpdated$.next(true);
  }

  protected _sortWatchMediaByName(watchA: any, watchB: any) {
    const nameA = watchA.name.toLowerCase();
    const nameB = watchB.name.toLowerCase();
    if (nameA < nameB) {
      return -1;
    }
    if (nameA > nameB) {
      return 1;
    }
    // equal
    return 0;
  }
}
