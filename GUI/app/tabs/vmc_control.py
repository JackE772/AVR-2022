from __future__ import annotations
#from pynput import keyboard

import functools
import json
import base64
import time
import time

from typing import List, Literal, Tuple

from bell.avr.mqtt.payloads import (
    AvrPcmSetBaseColorPayload,
    AvrPcmSetServoAbsPayload,
    AvrPcmSetServoOpenClosePayload,
    AvrApriltagsVisiblePayload,
    #AvrAprilTagsFpsPayload
)
from PySide6 import QtCore, QtWidgets
from numpy import cumprod

from ..lib.color import wrap_text
from .base import BaseTabWidget

class VMCControlWidget(BaseTabWidget):

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("VMC Control")

        #drop distance defintions (mm)
        self.nearZone = 40
        self.dropZone = 20

        #time interval between actions
        self.timeInterval = 1

        #led strip colors
        self.colorPurple = (10, 160, 32, 240)
        self.colorRed = (255, 255, 0, 0)
        self.colorBlue = (255, 0, 0, 255)
        self.colorGreen = (255, 0, 255, 0)
        self.colorYellow = (255, 255, 255, 0)
        self.colorBlank = (0,0,0,0)

        #servo parameters
        self.servoPin = 7
        self.openPulse = 800
        self.closePulse = 2000

        #STATIC state variables
        self.UNARMED = 0
        self.ARMED = 1
        self.DROPPING = 2

        self.OPENING = 3
        self.CLOSING = 4

        self.augurPosition = 0;

        #time of the last drop
        self.lastDrop = 0

        self.actionCount = 0
        #number of drops wanted
        self.targetDropAction = 3

        #current state
        self.state = self.ARMED


    def build(self) -> None:
        """
        Build the GUI layout
        """
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)

    # Function to move the auger
    def moveAugur(self) -> None:
        #if drop complete, move to unarmed
        if(self.actionCount < 0):
            self.state = self.ARMED
            return
        #of drop in progress, toggle the augur
        self.toggleAugur()

        #updates time
        self.lastDrop = time.time()
        #updates drop count
        print(self.actionCount)
        self.actionCount -= 1

    #toggleAugur - will open or seal the augur based on the prior state
    def toggleAugur(self)->None:
        if(self.augurPosition != self.OPENING):
            self.augurPosition = self.OPENING
            self.drop()
        else:
            self.augurPosition = self.CLOSING
            self.seal()

    #seal - command the serve to close the augur to sealed position
    def seal(self)->None:
        self.set_servo_pos( self.servoPin, self.closePulse)
        self.set_led(self.colorBlue)

    #drop - command the servo to open the augur
    def drop(self)-> None:
        self.set_servo_pos(self.servoPin, self.openPulse)
        self.set_led(self.colorRed)


    def process_message(self, topic: str, payload: str) -> None:
        """
        Process an incoming message and update the appropriate component
        """
        if(self.state == self.DROPPING and time.time() > (self.lastDrop + self.timeInterval)):
            self.moveAugur()

        # discard topics we don't recognize
        elif topic == "avr/apriltags/visible":
            print("read topic")

            x_json = json.loads(payload)
            horizontal_dist = x_json["tags"][0]["horizontal_dist"]

            if(horizontal_dist < self.nearZone and horizontal_dist > self.dropZone):
                self.set_led(self.colorYellow)
            elif(horizontal_dist <= self.dropZone and self.state == self.ARMED):
                self.set_led(self.colorGreen)
                self.state = self.DROPPING
                self.actionCount = self.targetDropAction * 2


    def set_servo(self, number: int, action: Literal["open", "close"]) -> None:
        """
        Set a servo state
        """
        self.send_message(
            "avr/pcm/set_servo_open_close",
            AvrPcmSetServoOpenClosePayload(servo=number, action=action),
        )

    def set_led(self, color: Tuple[int, int, int, int]) -> None:
        """
        Set LED color
        """
        self.send_message(
            "avr/pcm/set_base_color", AvrPcmSetBaseColorPayload(wrgb=color)
        )

    def set_servo_pos(self, number: int, position: int) -> None:
        """
        Set a servo state
        """

        self.send_message(
            "avr/pcm/set_servo_abs",
            AvrPcmSetServoAbsPayload(servo=number, absolute=position),
        )
