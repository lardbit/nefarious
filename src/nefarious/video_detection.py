import os
import cv2
import random
import numpy as np

from nefarious.parsers.base import ParserBase
from nefarious.quality import video_extensions
from nefarious.utils import logger_background


class VideoDetect:
    CAPTURE_FRAME_SECONDS = 5  # capture frames every x seconds
    MIN_VIDEO_SIMILARITY_STD = .05  # "real" videos should be > .15 (from 0-1)
    MAX_VIDEO_DURATION_DIFFERENCE_RATIO = .2  # the duration should be within x% of the actual

    video_path: str
    video_capture = None
    video_similarity_std: float  # from 0-1
    frame_count: int
    frame_rate: int
    duration: float
    read_interval: int

    def __init__(self, video_path: str):
        logger_background.debug(f'VideoDetect: Initializing video capture {video_path}')
        # video capture
        self.video_path = video_path
        self.video_capture = cv2.VideoCapture(self.video_path)

        # get video information
        self.frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_rate = int(self.video_capture.get(cv2.CAP_PROP_FPS))
        self.read_interval = int((self.frame_rate * self.CAPTURE_FRAME_SECONDS) - 1)
        self.duration = self.frame_count / self.frame_rate

    @classmethod
    def has_valid_video_in_path(cls, path: str):
        # TODO - this doesn't handle bundles (rar/zip/tar etc) since it won't find any "media" files

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

    def is_correct_length(self, expected_duration: float):
        return abs(self.duration - expected_duration) / expected_duration < self.MAX_VIDEO_DURATION_DIFFERENCE_RATIO

    def is_too_similar(self):
        logger_background.info(f'[VIDEO_DETECTION] video_similarity_std {self.video_similarity_std=}, {self.MIN_VIDEO_SIMILARITY_STD=}, {self.video_path=}')
        return self.video_similarity_std <= self.MIN_VIDEO_SIMILARITY_STD

    def process_similarity(self):
        results = []
        histograms = []

        # generate histograms for every captured frame
        for i in range(self.frame_count):
            if i == 0 or i % self.read_interval == 0:
                success, image = self.video_capture.read()
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                histograms.append(cv2.calcHist([gray_image], [0], None, [256], [0, 256]))

        # randomize histograms and compare frame by frame
        random.shuffle(histograms)
        for i, histogram in enumerate(histograms):
            if i == len(histograms) - 1:
                break
            compared = cv2.compareHist(histograms[i], histograms[i + 1], cv2.HISTCMP_BHATTACHARYYA)
            results.append(compared)

        # calculate the standard deviation from the results
        self.video_similarity_std = float(np.std(results))

        logger_background.info('[VIDEO_DETECTION] "{}" has frame similarity standard deviation: {}'.format(self.video_path, self.video_similarity_std))
