from multiprocessing import Process
import cv2
import imutils


class Mask(Process):
    hsv = None
    range_color = None

    def __init__(self, queue):
        super(Mask, self).__init__()
        self.queue = queue

    def set_hsv(self, hsv):
        self.hsv = hsv

    def set_range_color(self, range_color):
        self.range_color = range_color

    def stop(self):
        self.running = False
        self.terminate()

    def run(self):
        mask = cv2.inRange(self.hsv, self.range_color[0], self.range_color[1])
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        self.queue.put([mask, cnts], block=False)
