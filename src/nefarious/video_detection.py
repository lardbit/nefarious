import cv2
import random
import numpy as np


class VideoDetect:
    MIN_VIDEO_SIMILARITY_STD = .05  # regular videos should be > .15
    video_path: str
    video_similarity_std: float

    def __init__(self, video_path):
        self.video_path = video_path

    def is_too_similar(self):
        return self.video_similarity_std <= self.MIN_VIDEO_SIMILARITY_STD

    def process_similarity(self):
        results = []
        histograms = []
        n = 1  # capture frame every n seconds

        # video capture
        video = cv2.VideoCapture(self.video_path)

        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_rate = int(video.get(cv2.CAP_PROP_FPS))
        read_interval = int((frame_rate * n) - 1)

        # generate histograms for every captured frame
        for i in range(frame_count):
            if i == 0 or i % read_interval == 0:
                success, image = video.read()
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                histograms.append(cv2.calcHist([gray_image], [0], None, [256], [0, 256]))

        # randomize histograms and compare frame by frame
        random.shuffle(histograms)
        for i, histogram in enumerate(histograms):
            if i == len(histograms) - 1:
                break
            compared = cv2.compareHist(histograms[i], histograms[i + 1], cv2.HISTCMP_BHATTACHARYYA)
            results.append(compared)

        self.video_similarity_std = float(np.std(results))

        print('[VIDEO_DETECTION] Frame similarity standard deviation: {}'.format(self.video_similarity_std))
