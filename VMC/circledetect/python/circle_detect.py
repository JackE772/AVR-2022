import cv2
import numpy as np
import time

from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import AvrThermalReadingPayload
from loguru import logger

#cap = cv2.VideoCapture(1)

class circle_detect(MQTTModule):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        logger.debug("Circle auto aim has camera")

    def send_circles(self, list) -> None: #list of (x, y, r) from circle(s)
        logger.debug(list)
        self.send_message(
            "avr/westlake/circledetect", list.tolist()
        )

    def check_for_circles(self):
        _, frame = self.cap.read()
        frame = cv2.medianBlur(frame, 5)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, param1=90, param2=80, minRadius=25, maxRadius=0)
        if circles is not None:
            detected_circles = np.uint16(np.around(circles))
            for (x, y, r) in detected_circles[0, :]:
                cv2.circle(frame, (x, y), r, (0, 255, 0), 2)
                cv2.circle(frame, (x, y), 1, (0, 0, 255), 4)
                if len(detected_circles) == 1:
                    self.send_circles(detected_circles)

    def run(self) -> None:
        self.run_non_blocking()

        while True:
            self.check_for_circles()
            time.sleep(.1)

if __name__=="__main__":
    detect = circle_detect()
    detect.run()
