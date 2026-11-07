import json
import os
import select
import subprocess
import time

from nefarious.parsers.base import ParserBase
from nefarious.quality import video_extensions
from nefarious.utils import logger_background


class VideoDetect:
    FROZEN_FRACTION_THRESHOLD = 0.90  # a frozen fraction above this marks the video as spam/too-similar
    MAX_ANALYSIS_SECONDS = 120  # bound the freeze scan; a fully-static spam video is static from frame 0

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
            analysis_seconds = min(total_duration, self._analysis_seconds())
            freeze_durations, early_exit = self._detect_freezes(analysis_seconds)
        except Exception as exc:
            logger_background.info(f'[VIDEO_DETECTION] invalid video for {self.video_path}: {exc}')
            self.is_valid = False
            self.total_duration = 0.0
            self.frozen_fraction = 1.0
            return

        self.is_valid = True
        self.total_duration = total_duration
        if early_exit:
            # ffmpeg was terminated once enough motion had accumulated, which proves
            # the video cannot exceed the frozen-fraction threshold.
            self.frozen_fraction = 0.0
        else:
            self.frozen_fraction = sum(freeze_durations) / analysis_seconds

        logger_background.info('[VIDEO_DETECTION] "{}" has frozen fraction: {}'.format(self.video_path, self.frozen_fraction))

    def _analysis_seconds(self) -> float:
        # Lazy import to avoid a circular import with nefarious.models.
        from nefarious.models import NefariousSettings
        try:
            return float(NefariousSettings.get().video_detection_analysis_seconds)
        except Exception as exc:
            logger_background.info(f'[VIDEO_DETECTION] failed to read configured analysis window, using default: {exc}')
            return self.MAX_ANALYSIS_SECONDS

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

    def _detect_freezes(self, analysis_seconds: float):
        command = [
            'ffmpeg', '-i', self.video_path, '-t', str(analysis_seconds),
            '-vf', 'freezedetect=n=0.001:d=2', '-map', '0:v:0', '-f', 'null',
            '-progress', 'pipe:1', '-',
        ]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        freeze_durations = []
        freeze_start = None
        elapsed = 0.0
        moving_threshold = (1 - self.FROZEN_FRACTION_THRESHOLD) * analysis_seconds
        deadline = time.monotonic() + 600

        stdout_fd = proc.stdout.fileno()
        stderr_fd = proc.stderr.fileno()
        stdout_buf = b''
        stderr_buf = b''
        stdout_open = True
        stderr_open = True

        def moving_duration():
            frozen = sum(freeze_durations)
            if freeze_start is not None:
                frozen += elapsed - freeze_start
            return elapsed - frozen

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._terminate(proc)
                raise ValueError('ffmpeg freeze detection timed out')

            fds = []
            if stdout_open:
                fds.append(stdout_fd)
            if stderr_open:
                fds.append(stderr_fd)
            if not fds:
                break

            readable, _, _ = select.select(fds, [], [], min(remaining, 1.0))
            if not readable:
                continue

            for fd in readable:
                if fd == stdout_fd:
                    chunk = os.read(stdout_fd, 65536)
                    if not chunk:
                        stdout_open = False
                        continue
                    stdout_buf += chunk
                    while b'\n' in stdout_buf:
                        line, stdout_buf = stdout_buf.split(b'\n', 1)
                        line_str = line.decode('utf-8', errors='replace')
                        # out_time_us/out_time_ms are both microseconds; parse whichever is present.
                        if line_str.startswith('out_time_us=') or line_str.startswith('out_time_ms='):
                            try:
                                elapsed = int(line_str.split('=', 1)[1].strip()) / 1_000_000.0
                            except ValueError:
                                pass
                    if moving_duration() >= moving_threshold:
                        self._terminate(proc)
                        return freeze_durations, True
                elif fd == stderr_fd:
                    chunk = os.read(stderr_fd, 65536)
                    if not chunk:
                        stderr_open = False
                        continue
                    stderr_buf += chunk
                    while b'\n' in stderr_buf:
                        line, stderr_buf = stderr_buf.split(b'\n', 1)
                        line_str = line.decode('utf-8', errors='replace')
                        if 'lavfi.freezedetect.freeze_start' in line_str:
                            freeze_start = self._freeze_value(line_str, 'freeze_start')
                        elif 'lavfi.freezedetect.freeze_end' in line_str:
                            freeze_end = self._freeze_value(line_str, 'freeze_end')
                            if freeze_start is not None:
                                freeze_durations.append(freeze_end - freeze_start)
                                freeze_start = None
                    if moving_duration() >= moving_threshold:
                        self._terminate(proc)
                        return freeze_durations, True

        returncode = proc.wait()
        proc.stdout.close()
        proc.stderr.close()
        if returncode != 0:
            raise ValueError('ffmpeg returned non-zero exit code')

        if freeze_start is not None:
            # freezedetect emits only freeze_start (no freeze_end) when a freeze lasts
            # to the end of the analyzed window/stream; recover it from the window length.
            freeze_durations.append(analysis_seconds - freeze_start)
        return freeze_durations, False

    def _terminate(self, proc):
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        proc.stdout.close()
        proc.stderr.close()

    def _freeze_value(self, line: str, key: str) -> float:
        return float(line.split(f'{key}:', 1)[1].strip().split()[0])
