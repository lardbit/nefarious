import { LocalStorage } from '@ngx-pwa/local-storage';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, mergeMap, tap } from 'rxjs/operators';
import * as _ from 'lodash';
import {forkJoin, Observable, of, Subject, zip} from 'rxjs';
import {webSocket, WebSocketSubject} from 'rxjs/webSocket';


@Injectable({
  providedIn: 'root'
})
export class ApiService {
  STORAGE_KEY_API_TOKEN = 'NEFARIOUS-API-TOKEN';
  STORAGE_KEY_USER = 'NEFARIOUS-USER';
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
  API_URL_GENRES_MOVIE = '/api/genres/movie/';
  API_URL_GENRES_TV = '/api/genres/tv/';
  API_URL_QUALITY_PROFILES = '/api/quality-profiles/';
  API_URL_GIT_COMMIT = '/api/git-commit/';

  SEARCH_MEDIA_TYPE_TV = 'tv';
  SEARCH_MEDIA_TYPE_MOVIE = 'movie';

  public user: any;
  public userToken: string;
  public users: any; // staff only list of all users
  public settings: any;
  public qualityProfiles: string[];
  public watchTVSeasons: any[] = [];
  public watchTVSeasonRequests: any[] = [];
  public watchTVEpisodes: any[] = [];
  public watchTVShows: any[] = [];
  public watchMovies: any[] = [];

  public mediaUpdated$ = new Subject<any>();

  protected _webSocket: WebSocketSubject<any>;


  constructor(
    private http: HttpClient,
    private localStorage: LocalStorage,
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
              return this.fetchCoreData();
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
      this.localStorage.getItem(this.STORAGE_KEY_API_TOKEN).pipe(
        map(
          (data: string) => {
            this.userToken = data;
            return this.userToken;
          }),
      ),
      this.localStorage.getItem(this.STORAGE_KEY_USER).pipe(
        map(
          (data) => {
            this.user = data;
            return this.user;
          }),
      )
    );
  }

  public isLoggedIn(): boolean {
    return !!this.userToken;
  }

  public fetchCoreData(): Observable<any> {
    return forkJoin(
      [
        this.fetchSettings().pipe(
          tap(() => {
            // only initialize when in production
            if (!this.settings.is_debug) {
              this._initWebSocket();
            }
          })
        ),
        this.fetchWatchTVShows(),
        this.fetchWatchTVSeasons(),
        this.fetchWatchTVSeasonRequests(),
        this.fetchWatchTVEpisodes(),
        this.fetchWatchMovies(),
        this.fetchQualityProfiles(),
      ]
    ).pipe(
      tap(() => {
        // alert any relevant components media has been updated
        this._alertMediaUpdated();
      })
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
          this.localStorage.setItem(this.STORAGE_KEY_USER, this.user).subscribe();
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
        })
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
        this.localStorage.setItem(this.STORAGE_KEY_API_TOKEN, this.userToken).subscribe(
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
    _.assign(params || {}, {
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
            const watchShow = _.find(this.watchTVShows, (show) => {
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
        }
        return data;
      }),
    );
  }

  public searchMedia(query: string, mediaType: string) {
    let params = {
      q: query,
      media_type: mediaType,
    };
    params = _.assign(params, this._defaultParams());
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
    params = _.assign(params, this._defaultParams());
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
    params = _.assign(params, this._defaultParams());
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
      map((data: any) => {
        this.watchTVSeasons = data;
        return this.watchTVSeasons;
      }),
    );
  }

  public fetchWatchTVSeasonRequests(params?: any) {
    params = params || {};
    const httpParams = new HttpParams({fromObject: params});
    return this.http.get(this.API_URL_WATCH_TV_SEASON_REQUEST, {params: httpParams, headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchTVSeasonRequests = data;
        return this.watchTVSeasonRequests;
      }),
    );
  }

  public fetchWatchMovies(params?: any) {
    params = params || {};
    const httpParams = new HttpParams({fromObject: params});

    return this.http.get(this.API_URL_WATCH_MOVIE, {params: httpParams, headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchMovies = data;
        return this.watchMovies;
      }),
    );
  }

  public fetchWatchTVEpisodes() {
    return this.http.get(this.API_URL_WATCH_TV_EPISODE, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchTVEpisodes = data;
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

  public watchTVShow(showId: number, name: string, posterImageUrl: string, releaseDate: string, autoWatchNewSeasons?: boolean) {
    const params = {
      tmdb_show_id: showId,
      name: name,
      poster_image_url: posterImageUrl,
      release_date: releaseDate,
      auto_watch: !!autoWatchNewSeasons,
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
    );
  }

  public watchTVEpisode(watchShowId: number, episodeId: number, seasonNumber: number, episodeNumber: number, releaseDate: string) {
    const params = {
      watch_tv_show: watchShowId,
      tmdb_episode_id: episodeId,
      season_number: seasonNumber,
      episode_number: episodeNumber,
      release_date: releaseDate,
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
    );
  }

  public watchTVSeasonRequest(watchShowId: number, seasonNumber: number, releaseDate: string) {
    const params = {
      watch_tv_show: watchShowId,
      season_number: seasonNumber,
      release_date: releaseDate,
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
    );
  }

  public unWatchTVShow(watchId) {
    return this.http.delete(`${this.API_URL_WATCH_TV_SHOW}${watchId}/`, {headers: this._requestHeaders()}).pipe(
      tap((data: any) => {
        // filter out records
        this.watchTVShows = _.filter(this.watchTVShows, (watch) => {
          return watch.id !== watchId;
        });
        this.watchTVSeasons = _.filter(this.watchTVSeasons, (watch) => {
          return watch.watch_tv_show !== watchId;
        });
        this.watchTVSeasonRequests = _.filter(this.watchTVSeasonRequests, (watch) => {
          return watch.watch_tv_show !== watchId;
        });
        this.watchTVEpisodes = _.filter(this.watchTVEpisodes, (watch) => {
          return watch.watch_tv_show !== watchId;
        });
      })
    );
  }

  public unWatchTVEpisode(watchId) {
    return this.http.delete(`${this.API_URL_WATCH_TV_EPISODE}${watchId}/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const foundIndex = _.findIndex(this.watchTVEpisodes, (watch) => {
          return watch.id === watchId;
        });
        if (foundIndex >= 0) {
          this.watchTVEpisodes.splice(foundIndex, 1);
        }
        return data;
      })
    );
  }

  public watchMovie(movieId: number, name: string, posterImageUrl: string, releaseDate: string, qualityProfileCustom?: string) {
    const params = {
      tmdb_movie_id: movieId,
      name: name,
      poster_image_url: posterImageUrl,
      quality_profile_custom: qualityProfileCustom,
      release_date: releaseDate,
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
    );
  }

  public unWatchMovie(watchId) {
    return this.http.delete(`${this.API_URL_WATCH_MOVIE}${watchId}/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        const foundIndex = _.findIndex(this.watchMovies, (watch) => {
          return watch.id === watchId;
        });
        if (foundIndex >= 0) {
          this.watchMovies.splice(foundIndex, 1);
        }
        return data;
      })
    );
  }

  public unWatchTVSeason(watchTVSeasonRequestId) {
    return this.http.delete(`${this.API_URL_WATCH_TV_SEASON_REQUEST}${watchTVSeasonRequestId}/`, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {

        // find the season request instance
        const foundWatchRequestIndex = _.findIndex(this.watchTVSeasonRequests, (watch) => {
          return watch.id === watchTVSeasonRequestId;
        });
        if (foundWatchRequestIndex === -1) {
          return;
        }

        // remove the season request
        const foundWatchRequest = this.watchTVSeasonRequests[foundWatchRequestIndex];
        this.watchTVSeasonRequests.splice(foundWatchRequestIndex, 1);

        // find and remove the watch seasons
        const foundWatchIndex = _.findIndex(this.watchTVSeasons, (watch) => {
          return foundWatchRequest.tmdb_show_id === watch.tmdb_show_id && foundWatchRequest.season_number === watch.season_number;
        });
        if (foundWatchIndex >= 0) {
          this.watchTVSeasons.splice(foundWatchIndex, 1);
        }

        return data;
      })
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
            _.assign(watchMovie, data);
          }
        });
        return data;
      }));
  }

  public blacklistRetryTVSeason(watchMediaId: number) {
    return this.http.post(`${this.API_URL_WATCH_TV_SEASON}${watchMediaId}/blacklist-auto-retry/`, null, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchTVSeasons.forEach((watchSeason) => {
          if (data.id === watchSeason.id) {
            _.assign(watchSeason, data);
          }
        });
        return data;
      }));
  }

  public blacklistRetryTVEpisode(watchMediaId: number) {
    return this.http.post(`${this.API_URL_WATCH_TV_EPISODE}${watchMediaId}/blacklist-auto-retry/`, null, {headers: this._requestHeaders()}).pipe(
      map((data: any) => {
        this.watchTVEpisodes.forEach((watchEpisode) => {
          if (data.id === watchEpisode.id) {
            _.assign(watchEpisode, data);
          }
        });
        return data;
      }));
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
    const watchMediaIndex = _.findIndex(mediaList, (media) => {
      return media.id === data['data'].id;
    });
    if (data['action'] === 'UPDATED') {
      // update existing media
      if (watchMediaIndex >= 0) {
        _.assign(mediaList[watchMediaIndex], data['data']);
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

    // alert any relevant components media has been updated
    this._alertMediaUpdated();
  }

  protected _fetchGenres(mediaType: string) {
    const url = mediaType === this.SEARCH_MEDIA_TYPE_MOVIE ? this.API_URL_GENRES_MOVIE : this.API_URL_GENRES_TV;
    const params = this._defaultParams();
    return this.http.get(url, {headers: this._requestHeaders(), params: params});
  }

  protected _discoverMedia(mediaType: string, params: any) {
    params = _.assign(params, this._defaultParams());
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

  protected _alertMediaUpdated() {
    this.mediaUpdated$.next(true);
  }
}
