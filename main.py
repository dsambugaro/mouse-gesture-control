from collections import deque
from imutils.video import VideoStream
from multiprocessing import Process, Queue
import numpy as np
import argparse
import cv2
import imutils
import time
import pyautogui

from Mask import Mask
from Simulation import Simulation


class Main(object):
    kernel = np.ones((7, 7), np.uint8)
    perform = False
    drag = False
    click_range = np.array([[158, 68, 46], [198, 255, 255]])
    pointer_range = np.array([[30, 63, 21], [70, 255, 255]])
    cursor_pos = (0, 0)
    last_click_pos = (0, 0)
    pos = (0, 0)
    pos_click = (0, 0)
    center_pointer = (0, 0)
    center_click = (0, 0)

    def __init__(self, args):
        self.pts = deque(maxlen=args["buffer"])

        if not args.get("video", False):
            self.vs = VideoStream(src=0).start()
        else:
            self.vs = cv2.VideoCapture(args["video"])
        time.sleep(2.0)

        self.pointer_range = self.calibrateColor('Pointer', self.pointer_range)
        self.click_range = self.calibrateColor('Click', self.click_range)
        print('\tCalibration Successfull...')
        print('pointer = {}'.format(self.pointer_range))
        print('click = {}'.format(self.click_range))
        cv2.namedWindow('Frame')

        print(
            '**********************************************************************'
        )
        print('\tPress P to turn ON and OFF mouse simulation.')
        print('\tPress C to display the centroid of various colours.')
        print('\tPress R to recalibrate color ranges.')
        print('\tPress ESC to exit.')
        print(
            '**********************************************************************'
        )

    def nothing(self, x):
        pass

    def calibrateColor(self, color, def_range):
        name = 'Calibrate ' + color
        cv2.namedWindow(name)
        cv2.createTrackbar('Hue', name, def_range[0][0] + 20, 180,
                           self.nothing)
        cv2.createTrackbar('Sat', name, def_range[0][1], 255, self.nothing)
        cv2.createTrackbar('Val', name, def_range[0][2], 255, self.nothing)

        queue = Queue()
        while True:
            frameinv = self.vs.read()
            frame = cv2.flip(frameinv, 1)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            hue = cv2.getTrackbarPos('Hue', name)
            sat = cv2.getTrackbarPos('Sat', name)
            val = cv2.getTrackbarPos('Val', name)

            lower = np.array([hue - 20, sat, val])
            upper = np.array([hue + 20, 255, 255])
            mask = Mask(queue)
            mask.set_hsv(hsv)
            mask.set_range_color([lower, upper])
            mask.start()
            result = [hsv]

            try:
                result = queue.get()
            except Exception as e:
                pass

            cv2.imshow(name, result[0])

            k = cv2.waitKey(5) & 0xFF
            if k == ord(' '):
                cv2.destroyWindow(name)
                return np.array([[hue - 20, sat, val], [hue + 20, 255, 255]])
            elif k == ord('d'):
                cv2.destroyWindow(name)
                return def_range
        mask.stop()
        mask.join()

    def changeStatus(self, key):
        if key == ord('p'):
            self.perform = not self.perform
            if self.perform:
                print('Mouse simulation ON...')
            else:
                print('Mouse simulation OFF...')

        elif key == ord('r'):
            print(
                '**********************************************************************'
            )
            print('\tYou have entered recalibration mode.')
            print(
                '\tUse the trackbars to calibrate and press SPACE when done.')
            print('\tPress D to use the default settings')
            print(
                '**********************************************************************'
            )

            self.pointer_range = self.calibrateColor('Pointer',
                                                     self.pointer_range)
            self.click_range = self.calibrateColor('Click', self.click_range)

        else:
            pass

    def distance(self, c1, c2):
        distance = pow(pow(c1[0] - c2[0], 2) + pow(c1[1] - c2[1], 2), 0.5)
        return distance

    def setCursorPos(self, yc, pyp):
        yp = np.zeros(2)
        if abs(yc[0] - pyp[0]) < 5 and abs(yc[1] - pyp[1]) < 5:
            yp[0] = yc[0] + .7 * (pyp[0] - yc[0])
            yp[1] = yc[1] + .7 * (pyp[1] - yc[1])
        else:
            yp[0] = yc[0] + .1 * (pyp[0] - yc[0])
            yp[1] = yc[1] + .1 * (pyp[1] - yc[1])
        return yp

    def run(self):
        queue_click = Queue()
        queue_pointer = Queue()
        queue_simulation = Queue(1)
        simulation = Simulation(queue_simulation)
        simulation.start()
        while True:
            frame = self.vs.read()
            frame = cv2.flip(frame, 1)
            frame = frame[1] if args.get("video", False) else frame
            if frame is None:
                break
            frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            mask_click = Mask(queue_click)
            mask_click.set_hsv(hsv)
            mask_click.set_range_color(self.click_range)
            mask_click.start()
            cnts_click = []
            try:
                dilated, cnts_click = queue_click.get()
            except Exception as e:
                pass

            mask_pointer = Mask(queue_pointer)
            mask_pointer.set_hsv(hsv)
            mask_pointer.set_range_color(self.pointer_range)
            mask_pointer.start()
            cnts_pointer = []
            try:
                dilated, cnts_pointer = queue_pointer.get()
            except Exception as e:
                pass

            self.cursor_pos = self.pos
            self.last_click_pos = self.pos_click

            if int(self.distance(self.cursor_pos,
                                 self.last_click_pos)) in list(range(40, 91)):
                self.drag = True
            else:
                self.drag = False

            if len(cnts_pointer) > 0:
                c_pointer = max(cnts_pointer, key=cv2.contourArea)
                ((x, y), radius_pointer) = cv2.minEnclosingCircle(c_pointer)
                M = cv2.moments(c_pointer)
                self.center_pointer = (int(M["m10"] / M["m00"]),
                                       int(M["m01"] / M["m00"]))
                if radius_pointer > 24:
                    cv2.circle(frame, (int(x), int(y)), int(radius_pointer),
                               (0, 255, 255), 2)
                    cv2.circle(frame, self.center_pointer, 5, (0, 0, 255), -1)

                    self.pos = self.setCursorPos(self.center_pointer,
                                                 self.cursor_pos)

                    try:
                        queue_simulation.put(
                            [self.cursor_pos, 'move', self.drag, self.perform],
                            block=False)
                    except Exception as e:
                        pass

                else:
                    self.pts.appendleft(None)

            if len(cnts_click) > 0:
                c_click = max(cnts_click, key=cv2.contourArea)
                ((x_click, y_click),
                 radius_click) = cv2.minEnclosingCircle(c_click)
                M_click = cv2.moments(c_click)
                self.center_click = (int(M_click["m10"] / M_click["m00"]),
                                     int(M_click["m01"] / M_click["m00"]))

                if radius_click > 24:
                    cv2.circle(frame, (int(x_click), int(y_click)),
                               int(radius_click), (0, 255, 255), 2)
                    cv2.circle(frame, self.center_click, 5, (0, 0, 255), -1)
                    self.pos_click = self.setCursorPos(self.center_click,
                                                       self.last_click_pos)

            for i in range(1, len(self.pts)):
                if self.pts[i - 1] is None or self.pts[i] is None:
                    continue

                thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
                cv2.line(frame, self.pts[i - 1], self.pts[i], (0, 0, 255),
                         thickness)

            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            self.changeStatus(key)

            if key == 27:
                break

        mask_click.stop()
        mask_pointer.stop()
        simulation.stop()

        mask_click.join()
        mask_pointer.join()
        simulation.join()

        if not args.get("video", False):
            self.vs.stop()

        else:
            self.vs.release()

        time.sleep(0.5)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", help="path to the (optional) video file")
    ap.add_argument("-b",
                    "--buffer",
                    type=int,
                    default=64,
                    help="max buffer size")
    args = vars(ap.parse_args())
    main = Main(args)
    main.run()
