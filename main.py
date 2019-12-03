# USAGE
# python ball_tracking.py --video ball_tracking_example.mp4
# python ball_tracking.py

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
import pyautogui

kernel = np.ones((7, 7), np.uint8)

perform = False
drag = False
click_range = np.array([[158, 68, 46], [198, 255, 255]])
pointer_range = np.array([[30, 63, 21], [70, 255, 255]])

def nothing(x):
    pass

def distance( c1, c2):
    distance = pow( pow(c1[0]-c2[0],2) + pow(c1[1]-c2[1],2) , 0.5)
    return distance

def calibrateColor(color, def_range):

    global kernel
    name = 'Calibrate ' + color
    cv2.namedWindow(name)
    cv2.createTrackbar('Hue', name, def_range[0][0]+20, 180, nothing)
    cv2.createTrackbar('Sat', name, def_range[0][1], 255, nothing)
    cv2.createTrackbar('Val', name, def_range[0][2], 255, nothing)
    while(1):
        frameinv = vs.read()
        frame = cv2.flip(frameinv, 1)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        hue = cv2.getTrackbarPos('Hue', name)
        sat = cv2.getTrackbarPos('Sat', name)
        val = cv2.getTrackbarPos('Val', name)

        lower = np.array([hue-20, sat, val])
        upper = np.array([hue+20, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)
        eroded = cv2.erode(mask, kernel, iterations=1)
        dilated = cv2.dilate(eroded, kernel, iterations=1)

        cv2.imshow(name, dilated)

        k = cv2.waitKey(5) & 0xFF
        if k == ord(' '):
            cv2.destroyWindow(name)
            return np.array([[hue-20, sat, val], [hue+20, 255, 255]])
        elif k == ord('d'):
            cv2.destroyWindow(name)
            return def_range


def changeStatus(key):
    global perform
    global pointer_range, click_range
    # toggle mouse simulation
    if key == ord('p'):
        perform = not perform
        if perform:
            print('Mouse simulation ON...')
        else:
            print('Mouse simulation OFF...')

    elif key == ord('r'):
        print('**********************************************************************')
        print('\tYou have entered recalibration mode.')
        print('\tUse the trackbars to calibrate and press SPACE when done.')
        print('\tPress D to use the default settings')
        print('**********************************************************************')

        pointer_range = calibrateColor('Pointer', pointer_range)
        click_range = calibrateColor('Click', click_range)

    else:
        pass


def setCursorPos(yc, pyp):
    yp = np.zeros(2)
    if abs(yc[0]-pyp[0]) < 5 and abs(yc[1]-pyp[1]) < 5:
        yp[0] = yc[0] + .7*(pyp[0]-yc[0])
        yp[1] = yc[1] + .7*(pyp[1]-yc[1])
    else:
        yp[0] = yc[0] + .1*(pyp[0]-yc[0])
        yp[1] = yc[1] + .1*(pyp[1]-yc[1])
    return yp


def performAction(yp, action, drag, perform=True):

    if perform:
        cursor[0] = 4*(yp[0]-110)
        cursor[1] = 4*(yp[1]-120)
        if action == 'move':

            if yp[0] > 110 and yp[0] < 590 and yp[1] > 120 and yp[1] < 390:
                pyautogui.moveTo(cursor[0], cursor[1])
            elif yp[0] < 110 and yp[1] > 120 and yp[1] < 390:
                pyautogui.moveTo(8, cursor[1])
            elif yp[0] > 590 and yp[1] > 120 and yp[1] < 390:
                pyautogui.moveTo(1912, cursor[1])
            elif yp[0] > 110 and yp[0] < 590 and yp[1] < 120:
                pyautogui.moveTo(cursor[0], 8)
            elif yp[0] > 110 and yp[0] < 590 and yp[1] > 390:
                pyautogui.moveTo(cursor[0], 1072)
            elif yp[0] < 110 and yp[1] < 120:
                pyautogui.moveTo(8, 8)
            elif yp[0] < 110 and yp[1] > 390:
                pyautogui.moveTo(8, 1072)
            elif yp[0] > 590 and yp[1] > 390:
                pyautogui.moveTo(1912, 1072)
            else:
                pyautogui.moveTo(1912, 8)
        if drag:
            pyautogui.mouseDown()
        else:
            pyautogui.mouseUp()


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
                help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64,
                help="max buffer size")
args = vars(ap.parse_args())


# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points

pts = deque(maxlen=args["buffer"])

# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
    vs = VideoStream(src=0).start()

# otherwise, grab a reference to the video file
else:
    vs = cv2.VideoCapture(args["video"])

# allow the camera or video file to warm up
time.sleep(2.0)

cursor = [960, 540]
cursor_pos = (0, 0)
last_click_pos = (0, 0)
pos = (0, 0)
pos_click = (0, 0)


pointer_range = calibrateColor('Pointer', pointer_range)
click_range = calibrateColor('Click', click_range)
print('\tCalibration Successfull...')
print('pointer = {}'.format(pointer_range))
print('click = {}'.format(click_range))
cv2.namedWindow('Frame')

print('**********************************************************************')
print('\tPress P to turn ON and OFF mouse simulation.')
print('\tPress C to display the centroid of various colours.')
print('\tPress R to recalibrate color ranges.')
print('\tPress ESC to exit.')
print('**********************************************************************')

# keep looping
while True:
    # grab the current frame
    frame = vs.read()
    frame = cv2.flip(frame,1)

    # handle the frame from VideoCapture or VideoStream
    frame = frame[1] if args.get("video", False) else frame

    # if we are viewing a video and we did not grab a frame,
    # then we have reached the end of the video
    if frame is None:
        break

    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=600)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask_click = cv2.inRange(hsv, click_range[0], click_range[1])
    mask_click = cv2.erode(mask_click, None, iterations=2)
    mask_click = cv2.dilate(mask_click, None, iterations=2)

    mask_pointer = cv2.inRange(hsv, pointer_range[0], pointer_range[1])
    mask_pointer = cv2.erode(mask_pointer, None, iterations=2)
    mask_pointer = cv2.dilate(mask_pointer, None, iterations=2)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts_pointer = cv2.findContours(mask_pointer.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    cnts_pointer = imutils.grab_contours(cnts_pointer)

    cnts_click = cv2.findContours(mask_click.copy(), cv2.RETR_EXTERNAL,
                                  cv2.CHAIN_APPROX_SIMPLE)
    cnts_click = imutils.grab_contours(cnts_click)

    center_pointer = (0, 0)
    center_click = (0, 0)
    cursor_pos = pos
    last_click_pos = pos_click
    
    if int(distance(cursor_pos,last_click_pos)) in list(range(40, 91)):
        drag = True
    else:
        drag = False

    # only proceed if at least one contour was found
    if len(cnts_pointer) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c_pointer = max(cnts_pointer, key=cv2.contourArea)
        ((x, y), radius_pointer) = cv2.minEnclosingCircle(c_pointer)
        M = cv2.moments(c_pointer)
        center_pointer = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

        # only proceed if the radius meets a minimum size
        if radius_pointer > 24:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(
                radius_pointer), (0, 255, 255), 2)
            cv2.circle(frame, center_pointer, 5, (0, 0, 255), -1)

            pos = setCursorPos(center_pointer, cursor_pos)
            # update the points queue
            # pts.appendleft(center_green)

            performAction(cursor_pos, 'move', drag=drag, perform=perform)

        else:
            pts.appendleft(None)

    # only proceed if at least one contour was found
    if len(cnts_click) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c_click = max(cnts_click, key=cv2.contourArea)
        ((x_click, y_click), radius_click) = cv2.minEnclosingCircle(c_click)
        M_click = cv2.moments(c_click)
        center_click = (int(M_click["m10"] / M_click["m00"]),
                        int(M_click["m01"] / M_click["m00"]))

        # only proceed if the radius meets a minimum size
        if radius_click > 24:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x_click), int(y_click)),
                       int(radius_click), (0, 255, 255), 2)
            cv2.circle(frame, center_click, 5, (0, 0, 255), -1)
            pos_click = setCursorPos(center_click, last_click_pos)

    # loop over the set of tracked points
    for i in range(1, len(pts)):
        # if either of the tracked points are None, ignore
        # them
        if pts[i - 1] is None or pts[i] is None:
            continue

        # otherwise, compute the thickness of the line and
        # draw the connecting lines
        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

    # show the frame to our screen
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    changeStatus(key)

    # if the 'ESC' key is pressed, stop the loop
    if key == 27:
        break

# if we are not using a video file, stop the camera video stream
if not args.get("video", False):
    vs.stop()

# otherwise, release the camera
else:
    vs.release()

# close all windows
cv2.destroyAllWindows()
