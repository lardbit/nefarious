import os
import logging
import tmdbsimple as tmdb
from nefarious.celery import app
from nefarious.models import NefariousSettings, WatchTVEpisode, WatchTVShow, WatchMovie, TorrentBlacklist
from nefarious.parsers.movie import MovieParser
from nefarious.parsers.tv import TVParser
from nefarious.search import SearchTorrents, MEDIA_TYPE_TV, MEDIA_TYPE_MOVIE
from nefarious.tmdb import get_tmdb_client
from nefarious.transmission import get_transmission_client
from nefarious.utils import get_best_torrent_result


@app.task
def watch_tv_show_season_task(watch_tv_show_id: int, season_number: int):
    success = False
    tv_parser = TVParser()
    nefarious_settings = NefariousSettings.objects.all().get()
    tmdb.API_KEY = nefarious_settings.tmdb_token
    watch_tv_show = WatchTVShow.objects.get(pk=watch_tv_show_id)

    # load show from tmdb
    show_result = tmdb.TV(watch_tv_show.tmdb_show_id)
    show = show_result.info()

    valid_search_results = []

    search = SearchTorrents(MEDIA_TYPE_TV, show['name'])
    if search.ok:
        for result in search.results['Results']:
            match = tv_parser.parse(result['Title'])
            # match whole season only
            if match and 'season' in match and 'episode' not in match:
                if season_number in match['season']:
                    logging.info('Valid Match: {} - Season {} with Season {}'.format(
                        show['name'], season_number, match['season']))
                    valid_search_results.append(result)
            else:
                logging.info('Not matched: {}'.format(result['Title']))

        if valid_search_results:

            # find the torrent result with the highest weight (i.e seeds)
            best_result = get_best_torrent_result(valid_search_results, nefarious_settings)

            logging.info('Adding torrent for {} - Season {}'.format(show['name'], season_number))
            logging.info('Adding torrent {}'.format(best_result['Title']))

            # add to transmission
            transmission_client = get_transmission_client(nefarious_settings)
            transmission_session = transmission_client.session_stats()
            torrent = transmission_client.add_torrent(
                best_result['torrent_url'],
                paused=True,
                download_dir=os.path.join(
                    transmission_session.download_dir, nefarious_settings.transmission_tv_download_dir.lstrip('/')))

            # save torrent response on our watch tv episode instances
            for watch_tv_episode in watch_tv_show.watchtvepisode_set.all():
                # they'll all be the same transmission id since it's a full season torrent
                watch_tv_episode.transmission_torrent_id = torrent.id
                watch_tv_episode.transmission_torrent_hash = torrent.hashString
                watch_tv_episode.save()

            success = True

        else:
            logging.info('No valid search results for {} - Season {}'.format(
                show['name'], season_number))

    # individually download each episode since the full season couldn't be found
    if not success:
        logging.info('{} - Season {} could not be downloaded so downloading individual episodes'.format(
            show['name'], season_number))
        for watch_tv_episode in watch_tv_show.watchtvepisode_set.filter(season_number=season_number):
            watch_tv_episode_task(watch_tv_episode.id)


@app.task
def watch_tv_episode_task(watch_tv_episode_id: int):
    tv_parser = TVParser()
    nefarious_settings = NefariousSettings.objects.all().get()
    tmdb.API_KEY = nefarious_settings.tmdb_token
    watch_tv_episode = WatchTVEpisode.objects.get(pk=watch_tv_episode_id)

    # load show & episode from tmdb
    show_result = tmdb.TV(watch_tv_episode.watch_tv_show.tmdb_show_id)
    show = show_result.info()
    episode_result = tmdb.TV_Episodes(watch_tv_episode.watch_tv_show.tmdb_show_id, watch_tv_episode.season_number, watch_tv_episode.episode_number)
    episode = episode_result.info()

    valid_search_results = []

    # search torrents
    search = SearchTorrents(MEDIA_TYPE_TV, show['name'])
    if search.ok:
        for result in search.results['Results']:
            match = tv_parser.parse(result['Title'])
            if match and 'season' in match and 'episode' in match:
                if episode['season_number'] in match['season'] and episode['episode_number'] in match['episode']:
                    logging.info('Valid Match: {} - {}x{} with {}x{}'.format(
                        show['name'], episode['season_number'], episode['episode_number'],
                        match['season'], match['episode']))
                    valid_search_results.append(result)
            else:
                logging.info('Not matched: {}'.format(result['Title']))

        if valid_search_results:

            # find the torrent result with the highest weight (i.e seeds)
            best_result = get_best_torrent_result(valid_search_results, nefarious_settings)

            logging.info('Adding torrent for {} - {}x{}'.format(show['name'], episode['season_number'], episode['episode_number']))
            logging.info('Adding torrent {} with {} seeders'.format(best_result['Title'], best_result['Seeders']))

            # add to transmission
            transmission_client = get_transmission_client(nefarious_settings)
            transmission_session = transmission_client.session_stats()
            torrent = transmission_client.add_torrent(
                best_result['torrent_url'],
                paused=True,
                download_dir=os.path.join(
                    transmission_session.download_dir, nefarious_settings.transmission_tv_download_dir.lstrip('/')))

            # save torrent response on our watch instance
            watch_tv_episode.transmission_torrent_id = torrent.id
            watch_tv_episode.transmission_torrent_hash = torrent.hashString
            watch_tv_episode.save()
        else:
            logging.info('No valid search results for {} {}x{}'.format(
                show['name'], episode['season_number'], episode['episode_number']))
    else:
        logging.info('Search error: {}'.format(search.error_content))


@app.task
def watch_movie_task(watch_movie_id: int):
    movie_parser = MovieParser()
    nefarious_settings = NefariousSettings.objects.all().get()
    tmdb.API_KEY = nefarious_settings.tmdb_token
    watch_movie = WatchMovie.objects.get(pk=watch_movie_id)

    # load movie
    movie_result = tmdb.Movies(watch_movie.tmdb_movie_id)
    movie = movie_result.info()

    valid_search_results = []

    # search torrents
    search = SearchTorrents(MEDIA_TYPE_MOVIE, movie['original_title'])
    if search.ok:
        for result in search.results['Results']:
            match = movie_parser.parse(result['Title'])
            if match and match['title'] == movie_parser.normalize_media_title(movie['original_title']):
                valid_search_results.append(result)
            else:
                logging.info('Not matched: {}'.format(result['Title']))

        if valid_search_results:

            while valid_search_results:

                # find the torrent result with the highest weight (i.e seeds)
                best_result = get_best_torrent_result(valid_search_results, nefarious_settings)

                # add to transmission
                transmission_client = get_transmission_client(nefarious_settings)
                transmission_session = transmission_client.session_stats()

                torrent = transmission_client.add_torrent(
                    best_result['torrent_url'],
                    paused=True,  # start paused so we can verify this torrent hasn't been blacklisted - then start it
                    download_dir=os.path.join(
                        transmission_session.download_dir, nefarious_settings.transmission_movie_download_dir.lstrip('/')))

                # verify it's not blacklisted and save & start this torrent
                if not TorrentBlacklist.objects.filter(hash=torrent.hashString).exists():
                    logging.info('Adding torrent for {}'.format(movie['original_title']))
                    logging.info('Adding torrent {} with {} seeders'.format(best_result['Title'], best_result['Seeders']))
                    logging.info('Starting torrent id: {}'.format(torrent.id))
                    # save torrent details on our watch instance
                    watch_movie.transmission_torrent_id = torrent.id
                    watch_movie.transmission_torrent_hash = torrent.hashString
                    watch_movie.save()
                    # start the torrent
                    torrent.start()
                    break
                else:
                    # remove the blacklisted/paused torrent and continue to the next result
                    logging.info('BLACKLISTED: {} ({}) - trying next best result'.format(best_result['Title'], torrent.hashString))
                    transmission_client.remove_torrent([torrent.id])
                    valid_search_results.pop()
        else:
            logging.info('No valid search results for {}'.format(movie['original_title']))
    else:
        logging.info('Search error: {}'.format(search.error_content))


@app.task
def refresh_tmdb_configuration():

    logging.info('Refreshing TMDB Configuration')

    nefarious_settings = NefariousSettings.objects.get()

    tmdb_client = get_tmdb_client(nefarious_settings)
    configuration = tmdb_client.Configuration()

    nefarious_settings.tmdb_configuration = configuration.info()
    nefarious_settings.save()

    return nefarious_settings.tmdb_configuration
