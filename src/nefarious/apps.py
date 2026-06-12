from django.apps import AppConfig


class AppConfig(AppConfig):
    name = 'nefarious'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        """
        - include custom signals
        - load modules during development for auto-reload functionality (watch on changes)
        """
        import nefarious.parsers  # noqa
        import nefarious.tasks  # noqa
        import nefarious.signals  # noqa
