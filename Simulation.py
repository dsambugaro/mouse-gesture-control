from multiprocessing import Process

import pyautogui


class Simulation(Process):
    cursor = [960, 540]
    running = True

    def __init__(self, queue):
        super(Simulation, self).__init__()
        self.queue = queue

    def performAction(self, yp, action, drag, perform=True):
        if perform:
            self.cursor[0] = 4 * (yp[0] - 110)
            self.cursor[1] = 4 * (yp[1] - 120)
            if action == 'move':

                if yp[0] > 110 and yp[0] < 590 and yp[1] > 120 and yp[1] < 390:
                    pyautogui.moveTo(self.cursor[0], self.cursor[1])
                elif yp[0] < 110 and yp[1] > 120 and yp[1] < 390:
                    pyautogui.moveTo(8, self.cursor[1])
                elif yp[0] > 590 and yp[1] > 120 and yp[1] < 390:
                    pyautogui.moveTo(1912, self.cursor[1])
                elif yp[0] > 110 and yp[0] < 590 and yp[1] < 120:
                    pyautogui.moveTo(self.cursor[0], 8)
                elif yp[0] > 110 and yp[0] < 590 and yp[1] > 390:
                    pyautogui.moveTo(self.cursor[0], 1072)
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

    def stop(self):
        self.running = False
        self.terminate()

    def run(self):
        while self.running:
            if not self.queue.empty():
                params = self.queue.get()
                self.performAction(params[0], params[1], params[2], params[3])
