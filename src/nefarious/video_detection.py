import os
import random
import subprocess
import numpy as np

from nefarious.parsers.base import ParserBase
from nefarious.quality import video_extensions
from nefarious.utils import logger_background


class VideoDetect:
    MIN_VIDEO_SIMILARITY_STD = .05  # "real" videos should be > .15 (from 0-1)
    NUM_CAPTURE_FRAMES = 100
    SAMPLE_WIDTH = 128
    SAMPLE_HEIGHT = 72
    ANALYSIS_TIMEOUT_SECONDS = 600

    video_path: str
    video_similarity_std: float | None  # None means analysis was inconclusive

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.video_similarity_std = None

    @classmethod
    def has_valid_video_in_path(cls, path: str):
        # NOTE this doesn't handle bundles (rar/zip/tar etc.) since it won't find any "media" files

        files_to_verify = []

        if os.path.isdir(path):  # directory
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    files_to_verify.append(file_path)
        else:  # individual file
            files_to_verify = [path]

        logger_background.info(f'[VIDEO_DETECTION] files to verify: {", ".join(files_to_verify)}')

        for file_path in files_to_verify:
            file_extension_match = ParserBase.file_extension_regex.search(file_path)
            # skip sample videos
            if ParserBase.sample_file_regex.search(file_path):
                logger_background.info(f'[VIDEO_DETECTION] skipping "sample" file for {file_path}')
                continue
            # skip files that don't have extensions
            if not file_extension_match:
                logger_background.info(f'[VIDEO_DETECTION] skipping non-file-extension-match for {file_path}')
                continue
            file_extension = file_extension_match.group()
            # skip files that don't look like videos
            if file_extension not in video_extensions():
                logger_background.info(f'[VIDEO_DETECTION] skipping bad video_extension for {file_path}')
                continue
            detection = cls(file_path)
            detection.process_similarity()
            if not detection.is_too_similar():
                return True
            else:
                logger_background.info(f'[VIDEO_DETECTION] too similar for {file_path}')
        logger_background.warning(f'[VIDEO_DETECTION] no valid files found in {path}')
        return False

    def is_too_similar(self):
        logger_background.info(f'[VIDEO_DETECTION] video_similarity_std {self.video_similarity_std=}, {self.MIN_VIDEO_SIMILARITY_STD=}, {self.video_path=}')
        return self.video_similarity_std is not None and self.video_similarity_std <= self.MIN_VIDEO_SIMILARITY_STD

    def process_similarity(self):
        # Inconclusive analysis must not blacklist a potentially valid download.
        self.video_similarity_std = None
        try:
            result = subprocess.run([
                # Discard non-key packets in the demuxer as well as skipping
                # non-key frames in the decoder, avoiding unnecessary parsing.
                'ffmpeg', '-nostdin', '-v', 'error', '-xerror',
                '-discard', 'nokey', '-skip_frame', 'nokey',
                '-i', self.video_path, '-map', '0:v:0', '-an', '-sn', '-dn',
                '-vf', f'scale={self.SAMPLE_WIDTH}:{self.SAMPLE_HEIGHT},format=gray',
                '-fps_mode', 'passthrough', '-f', 'rawvideo', 'pipe:1',
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=self.ANALYSIS_TIMEOUT_SECONDS, check=True)
            frame_size = self.SAMPLE_WIDTH * self.SAMPLE_HEIGHT
            if len(result.stdout) % frame_size:
                raise ValueError('incomplete frame from ffmpeg')
            frames = np.frombuffer(result.stdout, dtype=np.uint8).reshape(-1, frame_size)
            if len(frames) < 3:
                # At least two distances are needed to measure their variance.
                raise ValueError('too few keyframes to compare')
            # Cover the whole file rather than concentrating on an intro or scene.
            indices = np.linspace(0, len(frames) - 1, min(len(frames), self.NUM_CAPTURE_FRAMES), dtype=int)
            histograms = [np.bincount(frames[i], minlength=256).astype(float) for i in indices]
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            logger_background.warning(f'[VIDEO_DETECTION] unable to analyze {self.video_path}; skipping spam classification: {exc}')
            return

        random.shuffle(histograms)
        results = [self._histogram_distance(a, b) for a, b in zip(histograms, histograms[1:])]
        self.video_similarity_std = float(np.std(results))

        logger_background.info('[VIDEO_DETECTION] "{}" has frame similarity standard deviation: {}'.format(self.video_path, self.video_similarity_std))

    @staticmethod
    def _histogram_distance(a: np.ndarray, b: np.ndarray) -> float:
        # OpenCV HISTCMP_BHATTACHARYYA (Hellinger), not -log(coefficient).
        coefficient = np.sqrt(a * b).sum() / np.sqrt(a.sum() * b.sum())
        return float(np.sqrt(np.clip(1.0 - coefficient, 0.0, 1.0)))
