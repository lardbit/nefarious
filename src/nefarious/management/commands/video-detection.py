from nefarious.video_detection import VideoDetect
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Inspects a video file to determine how accurate it is'

    def add_arguments(self, parser):
        parser.add_argument('video_path', type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Testing video: {}'.format(options['video_path'])))
        detection = VideoDetect(options['video_path'])
        detection.process_similarity()
        if detection.is_too_similar():
            self.stdout.write(self.style.ERROR('Video frames too similar with std: {}'.format(detection.video_similarity_std)))
        else:
            self.stdout.write(self.style.SUCCESS('Video looks good with std: {}'.format(detection.video_similarity_std)))



