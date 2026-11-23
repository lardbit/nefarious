import os
import random
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import numpy as np
from django.test import SimpleTestCase

from nefarious.video_detection import VideoDetect


class VideoDetectionFailureTest(SimpleTestCase):
    def test_unavailable_or_failed_decoder_does_not_classify_as_spam(self):
        for error in (FileNotFoundError('ffmpeg'), subprocess.TimeoutExpired('ffmpeg', 600),
                      subprocess.CalledProcessError(1, 'ffmpeg')):
            with self.subTest(error=error), mock.patch('nefarious.video_detection.subprocess.run', side_effect=error):
                self.assertTrue(VideoDetect.has_valid_video_in_path('unreadable.mp4'))

    def test_insufficient_or_partial_frames_are_inconclusive(self):
        frame = bytes(VideoDetect.SAMPLE_WIDTH * VideoDetect.SAMPLE_HEIGHT)
        for output in (b'', frame, frame * 2, frame + b'x'):
            with self.subTest(length=len(output)), mock.patch(
                    'nefarious.video_detection.subprocess.run',
                    return_value=subprocess.CompletedProcess([], 0, stdout=output)):
                self.assertTrue(VideoDetect.has_valid_video_in_path('unreadable.mp4'))

    def test_histogram_distance_uses_opencv_hellinger_formula(self):
        a = np.zeros(256)
        b = np.zeros(256)
        a[0] = 4
        b[0], b[1] = 1, 3
        self.assertAlmostEqual(VideoDetect._histogram_distance(a, a), 0.0)
        self.assertAlmostEqual(VideoDetect._histogram_distance(a, b), np.sqrt(0.5))
        b[0], b[1] = 0, 4
        self.assertAlmostEqual(VideoDetect._histogram_distance(a, b), 1.0)


@unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg required')
class VideoDetectionIntegrationTest(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory = tempfile.TemporaryDirectory(prefix='video-detection-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.static_path = cls.make_video('static.mp4', 'color=c=black:s=320x240:r=24:d=5')
        # Motion alone need not change a histogram (e.g. a moving color chart).
        # Fades provide changing intensity distributions, like scene transitions.
        cls.moving_path = cls.make_video('moving.mp4',
                                        'testsrc=size=320x240:rate=24:duration=5,fade=t=in:d=2,fade=t=out:st=3:d=2')
        cls.garbage_path = os.path.join(cls.directory.name, 'garbage.mp4')
        with open(cls.garbage_path, 'wb') as stream:
            stream.write(b'not a video')

    @classmethod
    def make_video(cls, name: str, source: str) -> str:
        path = os.path.join(cls.directory.name, name)
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i', source,
                        '-c:v', 'libx264', '-g', '12', '-pix_fmt', 'yuv420p', path],
                       check=True, capture_output=True, timeout=30)
        return path

    def test_static_video_is_spam(self):
        self.assertFalse(VideoDetect.has_valid_video_in_path(self.static_path))

    def test_moving_video_is_valid(self):
        with mock.patch('nefarious.video_detection.random.shuffle', side_effect=random.Random(42).shuffle):
            self.assertTrue(VideoDetect.has_valid_video_in_path(self.moving_path))

    def test_corrupt_video_is_not_blacklisted(self):
        self.assertTrue(VideoDetect.has_valid_video_in_path(self.garbage_path))
