import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from django.test import TestCase

from nefarious.video_detection import VideoDetect


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe required')
class VideoDetectionTest(TestCase):
    temp_dir = None
    static_path = None
    moving_path = None
    garbage_path = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = tempfile.mkdtemp(prefix='video-detect-test-')
        cls.static_path = os.path.join(cls.temp_dir, 'static.mp4')
        cls.moving_path = os.path.join(cls.temp_dir, 'moving.mp4')
        cls.garbage_path = os.path.join(cls.temp_dir, 'garbage.mp4')

        # fully static single-frame video (solid black) -> detected as frozen/spam
        subprocess.run(
            ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:d=5',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', cls.static_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # continuously moving test pattern -> not frozen -> valid
        subprocess.run(
            ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=5:size=320x240:rate=24',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', cls.moving_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # a non-video file with a video extension -> ffprobe fails -> invalid
        with open(cls.garbage_path, 'wb') as fh:
            fh.write(b'not a video' * 1000)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_static_video_is_spam(self):
        self.assertFalse(VideoDetect.has_valid_video_in_path(self.static_path))

    def test_moving_video_is_valid(self):
        self.assertTrue(VideoDetect.has_valid_video_in_path(self.moving_path))

    def test_garbage_video_is_invalid(self):
        self.assertFalse(VideoDetect.has_valid_video_in_path(self.garbage_path))

    def test_static_video_longer_than_window_is_still_spam(self):
        # The frozen fraction denominator must be the analysis window, not the full
        # video duration; otherwise a long static video (window < duration) would be
        # computed as a low fraction and wrongly pass as valid. Drive the window via
        # the configured-setting read (not the class constant) so a short window still
        # classifies a longer static video as spam.
        with mock.patch.object(VideoDetect, '_analysis_seconds', return_value=2):
            self.assertFalse(VideoDetect.has_valid_video_in_path(self.static_path))

    def test_early_exit_yields_valid(self):
        # When ffmpeg is terminated early because enough motion accumulated (early_exit
        # True), process_similarity must map that to a non-spam result (frozen_fraction
        # 0.0) rather than leaving the default/div-by-zero path. Patch the detection
        # result while letting the real ffprobe probe run against a real moving fixture.
        with mock.patch.object(VideoDetect, '_detect_freezes', return_value=([], True)):
            self.assertTrue(VideoDetect.has_valid_video_in_path(self.moving_path))
