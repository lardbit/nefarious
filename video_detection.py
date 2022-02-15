import cv2
import random
import numpy as np


def analyze():
    results = []
    histograms = []
    n = 1  # capture frame every n seconds

    # video capture
    # video = cv2.VideoCapture('/home/danny/Documents/Spider Man No Way Home 2021 1080p.WEBRip.x265-RBG.mp4')
    video = cv2.VideoCapture('/home/danny/Documents/big_buck_bunny_1080p_h264.mov')

    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_rate = int(video.get(cv2.CAP_PROP_FPS))
    read_interval = int((frame_rate * n) - 1)

    # generate histograms for every captured frame
    for i in range(frame_count):
        if i == 0 or i % read_interval == 0:
            success, image = video.read()
            cv2.imwrite('/tmp/frames/frame-%d.jpg' % i, image)
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            histograms.append(cv2.calcHist([gray_image], [0], None, [256], [0, 256]))

    # randomize histograms and compare frame by frame
    random.shuffle(histograms)
    for i, histogram in enumerate(histograms):
        if i == len(histograms) - 1:
            break
        compared = cv2.compareHist(histograms[i], histograms[i + 1], cv2.HISTCMP_BHATTACHARYYA)
        results.append(compared)

    mean = np.mean(results)
    standard_deviation = np.std(results)

    print('STD: {}'.format(standard_deviation))
    print('Mean: {}'.format(mean))


if __name__ == '__main__':
    analyze()
