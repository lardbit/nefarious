import cv2
import random
import numpy as np


def analyze():
    results = []
    histograms = []

    # video capture
    # video = cv2.VideoCapture('/home/danny/Documents/Spider Man No Way Home 2021 1080p.WEBRip.x265-RBG.mp4')
    # video = cv2.VideoCapture('/home/danny/Videos/Leader brief - compute delta (error).mp4')
    video = cv2.VideoCapture('/home/danny/Documents/big_buck_bunny_1080p_h264.mov')
    n = 1  # every seconds
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_rate = int(video.get(cv2.CAP_PROP_FPS))
    read_interval = int((frame_rate * n) - 1)
    success, image = video.read()

    print(frame_count)
    print(frame_rate)
    print(read_interval)

    # generate histograms for every captured frame
    for i in range(frame_count):
        if video.grab() is False:
            break
        if not success:
            break
        if i % read_interval == 0:
            _, image = video.read()
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            histograms.append(cv2.calcHist([gray_image], [0], None, [256], [0, 256]))

    # TODO - shouldn't compare sequentially since they'll likely be similar anyway
    random.shuffle(histograms)

    # compare histograms frame by frame
    for i, histogram in enumerate(histograms):
        if i == len(histograms) - 1:
            break
        print(cv2.compareHist(histograms[0], histograms[1], cv2.HISTCMP_BHATTACHARYYA))
        results.append(cv2.compareHist(histograms[0], histograms[1], cv2.HISTCMP_BHATTACHARYYA))

    standard_deviation = np.std(results)
    print('STD: {}'.format(standard_deviation))


if __name__ == '__main__':
    analyze()
