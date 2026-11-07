import json
import os
import subprocess

from nefarious.parsers.base import ParserBase
from nefarious.quality import video_extensions
from nefarious.utils import logger_background


class VideoDetect:
    FROZEN_FRACTION_THRESHOLD = 0.90  # a frozen fraction above this marks the video as spam/too-similar

    video_path: str
    frozen_fraction: float  # from 0-1
    is_valid: bool
    total_duration: float

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.frozen_fraction = 0.0
        self.is_valid = False
        self.total_duration = 0.0

        logger_background.info(f'VideoDetect: Initializing video detection {video_path}')

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
        logger_background.info(f'[VIDEO_DETECTION] frozen_fraction {self.frozen_fraction=}, {self.FROZEN_FRACTION_THRESHOLD=}, {self.video_path=}')
        if not self.is_valid:
            return True
        return self.frozen_fraction > self.FROZEN_FRACTION_THRESHOLD

    def process_similarity(self):
        try:
            total_duration = self._probe_video()
            if total_duration < 1.0:
                raise ValueError(f'video duration too short: {total_duration}')
            freeze_durations = self._detect_freezes(total_duration)
        except Exception as exc:
            logger_background.info(f'[VIDEO_DETECTION] invalid video for {self.video_path}: {exc}')
            self.is_valid = False
            self.total_duration = 0.0
            self.frozen_fraction = 1.0
            return

        self.is_valid = True
        self.total_duration = total_duration
        total_freeze_duration = sum(freeze_durations)
        self.frozen_fraction = total_freeze_duration / total_duration

        logger_background.info('[VIDEO_DETECTION] "{}" has frozen fraction: {}'.format(self.video_path, self.frozen_fraction))

    def _probe_video(self) -> float:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-select_streams', 'v:0', self.video_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode != 0:
            raise ValueError('ffprobe returned non-zero exit code')
        data = json.loads(result.stdout.decode('utf-8'))
        streams = data.get('streams') or []
        if not streams:
            raise ValueError('no video stream found')
        duration = (data.get('format') or {}).get('duration')
        if duration is None:
            duration = streams[0].get('duration')
        if duration is None:
            raise ValueError('no duration available')
        return float(duration)

    def _detect_freezes(self, total_duration: float) -> list:
        result = subprocess.run(
            ['ffmpeg', '-i', self.video_path, '-vf', 'freezedetect=n=0.001:d=2', '-map', '0:v:0', '-f', 'null', '-'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        if result.returncode != 0:
            raise ValueError('ffmpeg returned non-zero exit code')
        freeze_durations = []
        freeze_start = None
        for line in result.stderr.decode('utf-8', errors='replace').splitlines():
            if 'lavfi.freezedetect.freeze_start' in line:
                freeze_start = self._freeze_value(line, 'freeze_start')
            elif 'lavfi.freezedetect.freeze_end' in line:
                freeze_end = self._freeze_value(line, 'freeze_end')
                if freeze_start is not None:
                    freeze_durations.append(freeze_end - freeze_start)
                    freeze_start = None
        if freeze_start is not None:
            # freezedetect only reports freeze_start when a freeze lasts to the end of
            # the stream; it never emits freeze_end/freeze_duration for that final freeze.
            freeze_durations.append(total_duration - freeze_start)
        return freeze_durations

    def _freeze_value(self, line: str, key: str) -> float:
        return float(line.split(f'{key}:', 1)[1].strip().split()[0])
