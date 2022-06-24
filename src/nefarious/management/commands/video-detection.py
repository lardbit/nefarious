from nefarious.video_detection import VideoDetect
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Inspects a video file to determine how accurate it is'

    def add_arguments(self, parser):
        parser.add_argument('video_path', type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Testing videos in path: {}'.format(options['video_path'])))
        if not VideoDetect.has_valid_video_in_path(options['video_path']):
            self.stdout.write(self.style.ERROR('Video frames too similar'))
        else:
            self.stdout.write(self.style.SUCCESS('Found accurate looking videos'))



