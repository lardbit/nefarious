import os


class ImporterBase:
    download_path = None
    nefarious_settings = None
    tmdb_client = None
    tmdb_search = None
    user = None

    def __init__(self, nefarious_settings, download_path, tmdb_client, user):
        self.nefarious_settings = nefarious_settings
        self.download_path = download_path
        self.tmdb_client = tmdb_client
        self.tmdb_search = tmdb_client.Search()
        self.user = user

    def ingest(self, path):
        for file_name in os.listdir(path):
            self._ingest_path(path, file_name)

    def _ingest_path(self, path, file_name):
        raise NotImplementedError
