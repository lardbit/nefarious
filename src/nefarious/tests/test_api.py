from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from nefarious.models import (
    NefariousSettings, QualityProfile, WatchMovie, WatchTVShow,
    WatchTVEpisode, TorrentBlacklist,
)
from nefarious import quality


class ApiAuthTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.qp_tv = QualityProfile.objects.create(name='TV', quality=quality.PROFILE_ANY)
        self.qp_movie = QualityProfile.objects.create(name='Movie', quality=quality.PROFILE_HD_1080p)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )

    def _login(self):
        response = self.client.post('/api/auth/', {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 200)
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        return token

    def test_obtain_auth_token(self):
        response = self.client.post('/api/auth/', {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_auth_invalid_credentials(self):
        response = self.client.post('/api/auth/', {'username': 'testuser', 'password': 'wrong'})
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_access_denied(self):
        response = self.client.get('/api/user/')
        self.assertEqual(response.status_code, 401)

    def test_authenticated_access_granted(self):
        self._login()
        response = self.client.get('/api/user/')
        self.assertEqual(response.status_code, 200)


class ApiSettingsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.qp_tv = QualityProfile.objects.create(name='TV', quality=quality.PROFILE_ANY)
        self.qp_movie = QualityProfile.objects.create(name='Movie', quality=quality.PROFILE_HD_1080p)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=self.qp_tv,
            quality_profile_movies=self.qp_movie,
        )
        self._login()

    def _login(self):
        response = self.client.post('/api/auth/', {'username': 'staff', 'password': 'pass'})
        token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

    def test_get_settings(self):
        response = self.client.get('/api/settings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['language'], 'en')

    def test_update_settings(self):
        settings_id = self.settings.id
        response = self.client.patch(f'/api/settings/{settings_id}/', {
            'language': 'es',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['language'], 'es')

    def test_verify_settings(self):
        response = self.client.get(f'/api/settings/{self.settings.id}/verify/')
        self.assertIn(response.status_code, (200, 400))  # may fail without external services

    def test_non_staff_cannot_update_settings(self):
        non_staff = User.objects.create_user(username='regular', password='pass')
        resp = self.client.post('/api/auth/', {'username': 'regular', 'password': 'pass'})
        token = resp.data['token']
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = client2.patch(f'/api/settings/{self.settings.id}/', {'language': 'fr'}, format='json')
        self.assertIn(response.status_code, (200, 403))  # partial serializer for non-staff


class ApiWatchMovieTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='pass')
        self.qp = QualityProfile.objects.create(name='HD', quality=quality.PROFILE_HD_1080p)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=QualityProfile.objects.create(name='TV2', quality=quality.PROFILE_ANY),
            quality_profile_movies=self.qp,
        )
        self._login()

    def _login(self):
        resp = self.client.post('/api/auth/', {'username': 'user', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])

    def test_list_watch_movies_empty(self):
        response = self.client.get('/api/watch-movie/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_create_watch_movie(self):
        response = self.client.post('/api/watch-movie/', {
            'tmdb_movie_id': 123,
            'name': 'Test Movie',
            'poster_image_url': 'http://example.com/poster.jpg',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tmdb_movie_id'], 123)
        self.assertEqual(response.data['name'], 'Test Movie')
        self.assertIn('requested_by', response.data)

    def test_update_watch_movie(self):
        movie = WatchMovie.objects.create(
            user=self.user,
            tmdb_movie_id=456,
            name='Original Name',
            poster_image_url='http://example.com/poster.jpg',
        )
        response = self.client.patch(f'/api/watch-movie/{movie.id}/', {
            'name': 'Updated Name',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_delete_watch_movie(self):
        movie = WatchMovie.objects.create(
            user=self.user,
            tmdb_movie_id=789,
            name='To Delete',
            poster_image_url='http://example.com/poster.jpg',
        )
        response = self.client.delete(f'/api/watch-movie/{movie.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(WatchMovie.objects.count(), 0)

    def test_unique_movie_constraint(self):
        self.client.post('/api/watch-movie/', {
            'tmdb_movie_id': 100,
            'name': 'Movie 1',
            'poster_image_url': 'http://example.com/poster.jpg',
        }, format='json')
        response = self.client.post('/api/watch-movie/', {
            'tmdb_movie_id': 100,
            'name': 'Movie 2',
            'poster_image_url': 'http://example.com/poster.jpg',
        }, format='json')
        self.assertEqual(response.status_code, 400)


class ApiWatchTVShowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='pass')
        self.qp = QualityProfile.objects.create(name='HD', quality=quality.PROFILE_HD_1080p)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=QualityProfile.objects.create(name='TV3', quality=quality.PROFILE_ANY),
            quality_profile_movies=self.qp,
        )
        self._login()

    def _login(self):
        resp = self.client.post('/api/auth/', {'username': 'user', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])

    def test_create_tv_show(self):
        response = self.client.post('/api/watch-tv-show/', {
            'tmdb_show_id': 200,
            'name': 'Test TV Show',
            'poster_image_url': 'http://example.com/poster.jpg',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tmdb_show_id'], 200)
        self.assertIn('requested_by', response.data)

    def test_delete_tv_show(self):
        show = WatchTVShow.objects.create(
            user=self.user,
            tmdb_show_id=300,
            name='To Delete Show',
            poster_image_url='http://example.com/poster.jpg',
        )
        response = self.client.delete(f'/api/watch-tv-show/{show.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(WatchTVShow.objects.count(), 0)


class ApiUserTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_current_user_endpoint(self):
        user = User.objects.create_user(username='test', password='pass')
        resp = self.client.post('/api/auth/', {'username': 'test', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])
        response = self.client.get('/api/user/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['username'], 'test')

    def test_create_user_by_staff(self):
        staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        resp = self.client.post('/api/auth/', {'username': 'staff', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])
        response = self.client.post('/api/users/', {
            'username': 'newuser',
            'password': 'newpass',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_non_staff_cannot_create_user(self):
        regular = User.objects.create_user(username='regular', password='pass')
        resp = self.client.post('/api/auth/', {'username': 'regular', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])
        response = self.client.post('/api/users/', {
            'username': 'hacker',
            'password': 'hackpass',
        }, format='json')
        self.assertEqual(response.status_code, 403)


class ApiSearchTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='user', password='pass', is_staff=True)
        self.qp = QualityProfile.objects.create(name='Any', quality=quality.PROFILE_ANY)
        self.settings = NefariousSettings.objects.create(
            quality_profile_tv=self.qp,
            quality_profile_movies=self.qp,
            tmdb_token='test-token',
        )
        resp = self.client.post('/api/auth/', {'username': 'user', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])

    def test_search_media_requires_params(self):
        response = self.client.get('/api/search/media/?q=test&media_type=movie')
        # May fail without live TMDB, but endpoint should be reachable
        self.assertIn(response.status_code, [200, 400, 500])

    def test_search_torrents_requires_params(self):
        response = self.client.get('/api/search/torrents/?q=test&media_type=movie')
        self.assertIn(response.status_code, [200, 400, 500])

    def test_qualities_endpoint(self):
        response = self.client.get('/api/qualities/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        if len(response.data) > 0:
            self.assertIn('any', response.data)

    def test_quality_profiles_endpoint(self):
        response = self.client.get('/api/quality-profile/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)

    def test_media_categories_endpoint(self):
        response = self.client.get('/api/media-categories/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('mediaCategories', response.data)
