import cv2
import random
import numpy as np


class VideoDetect:
    CAPTURE_FRAME_SECONDS = 5  # capture frames every x seconds
    MIN_VIDEO_SIMILARITY_STD = .05  # "real" videos should be > .15
    MAX_VIDEO_DURATION_DIFFERENCE_RATIO = .2  # the duration should be within x% of the actual

    video_path: str
    video_capture = None
    video_similarity_std: float
    frame_count: int
    frame_rate: int
    duration: float
    read_interval: int

    def __init__(self, video_path: str):
        # video capture
        self.video_path = video_path
        self.video_capture = cv2.VideoCapture(self.video_path)

        # get video information
        self.frame_count = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_rate = int(self.video_capture.get(cv2.CAP_PROP_FPS))
        self.read_interval = int((self.frame_rate * self.CAPTURE_FRAME_SECONDS) - 1)
        self.duration = self.frame_count / self.frame_rate

    def is_correct_length(self, correct_duration: float):
        return abs(self.duration - correct_duration) / correct_duration < self.MAX_VIDEO_DURATION_DIFFERENCE_RATIO

    def is_too_similar(self):
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
