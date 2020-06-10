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

    def ingest_root(self, path):
        for root, dirs, files in os.walk(path):
            for file in files:
                self.ingest_path(os.path.join(root, file))

    def ingest_path(self, file_path):
        raise NotImplementedError

    def _is_dir(self, path) -> bool:
        # is a directory and NOT a symlink
        return os.path.isdir(path) and not os.path.islink(path)

    def _ingest_depth(self, path) -> int:
        root_depth = len(os.path.normpath(self.download_path).split(os.sep))
        path_depth = len(os.path.normpath(path).split(os.sep))
        # subtract 1 to account for the movies and tv subdirectories, i.e /download/path/tv & /download/path/movies
        return path_depth - root_depth - 1
