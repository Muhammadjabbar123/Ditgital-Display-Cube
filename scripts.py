# Create by Packetsss
# Personal use is allowed
# Commercial use is prohibited

import numpy as np
import cv2
from scipy import ndimage
import math
from copy import deepcopy


class Images:
    def __init__(self, img):
        self.img = cv2.imread(img, 1)
        # if self.img.shape[0] / self.img.shape[1] < 0.80:
           
        #     self.img_width = 1218
        #     self.img_height = 707
        #     #self.img_height = int(self.img_width * self.img.shape[0] / self.img.shape[1])
        # else:
           
        #     self.img_height = 900
        #     self.img_width = int(self.img_height * self.img.shape[1] / self.img.shape[0])

        # self.img = cv2.resize(self.img, (self.img_width, self.img_height))
        self.img_copy = deepcopy(self.img)
        self.grand_img_copy = deepcopy(self.img)

        self.img_name = img.split('\\')[-1].split(".")[0]
        self.img_format = img.split('\\')[-1].split(".")[1]

        self.left, self.right, self.top, self.bottom = None, None, None, None

        # self.bypass_censorship()

    def auto_contrast(self):
        clip_hist_percent = 20
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)

        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)
        accumulator = [float(hist[0])]
        for index in range(1, hist_size):
            accumulator.append(accumulator[index - 1] + float(hist[index]))
        maximum = accumulator[-1]
        clip_hist_percent *= (maximum / 100.0)
        clip_hist_percent /= 2.0
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1
        maximum_gray = hist_size - 1
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1
        alpha = 255 / (maximum_gray - minimum_gray)
        beta = -minimum_gray * alpha

        self.img = cv2.convertScaleAbs(self.img, alpha=alpha, beta=beta)

    def auto_sharpen(self):
        self.img = cv2.detailEnhance(self.img, sigma_s=10, sigma_r=0.3)

    def auto_cartoon(self, style=0):
        edges1 = cv2.bitwise_not(cv2.Canny(self.img, 100, 200))
        gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 7, 7)
        dst = cv2.edgePreservingFilter(self.img, flags=2, sigma_s=64, sigma_r=0.25)

        if not style:
            # less blurry
            self.img = cv2.bitwise_and(dst, dst, mask=edges1)
        else:
            # more blurry
            self.img = cv2.bitwise_and(dst, dst, mask=edges2)

    def auto_invert(self):
        self.img = cv2.bitwise_not(self.img)

    def change_b_c(self, alpha=1, beta=0):
        # contrast from 0 to 3, brightness from -100 to 100
        self.img = cv2.convertScaleAbs(self.img, alpha=alpha, beta=beta)

    def change_saturation(self, value):
        # -300 to 300
        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV).astype("float32")
        (h, s, v) = cv2.split(img_hsv)
        s += value
        s = np.clip(s, 0, 255)
        img_hsv = cv2.merge([h, s, v])
        self.img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    def remove_color(self, color):
        h = color.lstrip('#')
        color = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])

        img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV).astype("float32")
        low = np.array([color[0] - 15, 0, 20])
        high = np.array([color[0] + 15, 255, 255])
        mask = cv2.inRange(img_hsv, low, high)
        img_hsv[mask > 0] = (0, 0, 255)
        self.img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)



    def save_img(self, file):
        cv2.imwrite(file, self.img)

    def reset(self, flip=None):
        if flip is None:
            flip = [False, False]
        self.img = deepcopy(self.img_copy)
        if flip[0]:
            self.img = cv2.flip(self.img, 0)
        if flip[1]:
            self.img = cv2.flip(self.img, 1)

    def grand_reset(self):
        self.img = deepcopy(self.grand_img_copy)
        self.img_copy = deepcopy(self.grand_img_copy)


def main():
    path = "ppl.jpg"
    img = Images(path)
    img_name = path.split('\\')[-1].split(".")[0]

    cv2.imshow(img_name, img.img)
    cv2.waitKey()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
