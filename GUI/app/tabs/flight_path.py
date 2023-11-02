
import sys
import json
import time
from PySide6 import QtCore, QtWidgets
from .base import BaseTabWidget

import functools
from typing import List
from PySide6 import QtCore, QtWidgets

from ..lib.color import wrap_text

from bell.avr.mqtt.payloads import (
    AvrAutonomousBuildingDropPayload,
    AvrAutonomousEnablePayload,
    AvrApriltagsRawPayload,
    AvrApriltagsRawTags,
    AvrApriltagsSelectedPayload,
    AvrApriltagsVisiblePayload,
    AvrApriltagsVisibleTags,
    AvrApriltagsVisibleTagsPosWorld,
)


class AVRFlightPath(BaseTabWidget):
    def __init__ (self, parent: QtWidgets.QWidget):
        super().__init__(parent)
    
        self.setWindowTitle("AVR Auton Movement")
    def build(self) -> None:
        """
        Build the GUI layout
        """
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)

        # ==========================
        # Autonomous mode
        autonomous_groupbox = QtWidgets.QGroupBox("Autonomous")
        autonomous_layout = QtWidgets.QHBoxLayout()
        autonomous_groupbox.setLayout(autonomous_layout)

        autonomous_takeoff_button = QtWidgets.QPushButton("Takeoff")
        autonomous_takeoff_button.clicked.connect(lambda: self.takeoff())
        autonomous_layout.addWidget(autonomous_takeoff_button)

        autonomous_land_button = QtWidgets.QPushButton("Land")
        autonomous_land_button.clicked.connect(lambda: self.land())
        autonomous_layout.addWidget(autonomous_land_button)

        autonomous_approach_button = QtWidgets.QPushButton("Approach")
        autonomous_approach_button.clicked.connect(lambda: self.approach())
        autonomous_layout.addWidget(autonomous_approach_button)

        autonomous_returns_button = QtWidgets.QPushButton("Return Home")
        autonomous_returns_button.clicked.connect(lambda: self.returns())
        autonomous_layout.addWidget(autonomous_returns_button)

        autonomous_enable_scan_button = QtWidgets.QPushButton("Enable Scan")
        autonomous_enable_scan_button.clicked.connect(lambda: self.enable_scan())
        autonomous_layout.addWidget(autonomous_enable_scan_button)

        autonomous_disable_scan_button = QtWidgets.QPushButton("Disable Scan")
        autonomous_disable_scan_button.clicked.connect(lambda: self.disable_scan())
        autonomous_layout.addWidget(autonomous_disable_scan_button)

        set_origin_button = QtWidgets.QPushButton("Set Origin")
        set_origin_button.clicked.connect(lambda: self.set_origin())
        autonomous_layout.addWidget(set_origin_button)

        autonomous_mission_one_button = QtWidgets.QPushButton("AVR Mission 1")
        autonomous_mission_one_button.clicked.connect(lambda: self.mission_one())
        autonomous_layout.addWidget(autonomous_mission_one_button)

        autonomous_mission_two_button = QtWidgets.QPushButton("AVR Mission 2")
        autonomous_mission_two_button.clicked.connect(lambda: self.mission_two())
        autonomous_layout.addWidget(autonomous_mission_two_button)

        self.autonomous_label = QtWidgets.QLabel()
        self.autonomous_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        autonomous_layout.addWidget(self.autonomous_label)

        layout.addWidget(autonomous_groupbox, 0, 0, 1, 1)

    def setHome(self):

        self.send_message(
            "avr/fcm/capture_home", {}
        )

    def gotoNED(self, n, e, d, heading):

        # Define the values you want to include in the JSON structure
        action = "goto_location_ned"


        # Create the JSON structure as a dictionary
        data = {
            "action": action,
            "payload": {
                "n": n,
                "e": e,
                "d": d,
                "heading": heading
            }
        }

        # Convert the dictionary to a JSON string
        json_string = json.dumps(data, indent=4)  # The `indent` parameter adds formatting for readability
        # Print the JSON string
        print(json_string)

        self.send_message(
            "avr/fcm/actions", data
        )
    
    def sendTakeoff(self, alt):

        # Define the values you want to include in the JSON structure
        action = "takeoff"


        # Create the JSON structure as a dictionary
        data = {
            "action": action,
            "payload": {
                "alt": alt
            }
        }

        # Convert the dictionary to a JSON string
        json_string = json.dumps(data, indent=1)  # The `indent` parameter adds formatting for readability
        # Print the JSON string
        print(json_string)

        self.send_message(
            "avr/fcm/actions", data
        )

    def sendLand(self):

        # Define the values you want to include in the JSON structure
        action = "land"


        # Create the JSON structure as a dictionary
        data = {
            "action": action,
            "payload": {}
        }

        # Convert the dictionary to a JSON string
        json_string = json.dumps(data, indent=1)  # The `indent` parameter adds formatting for readability
        # Print the JSON string
        print(json_string)

        self.send_message(
            "avr/fcm/actions", data
        )

    def takeoff(self):
        #Fly upwards 3 meters/Takeoff
        alt = 3
        self.sendTakeoff(alt)

    def land(self):
        #Land the Drone
        self.sendLand()

    def approach(self):
        #Go towards Building
        n = 4.115 #From center of landing pad to edge of building 1 is 4.949m, building top is .61m, 5.559 ft real comp.
        e = -1.591 #To edge of building 1 is -1.359, -1.969 in real comp
        d = -3
        heading = 0
        self.gotoNED(n, e, d, heading)
        
    def returns(self):
        #Return to pad
        n = 0
        e = 0
        d = -3
        heading = 0
        self.gotoNED(n, e, d, heading)


    def enable_scan(self, value:int):
       print(f"this is value {value}")  
        

    def disable_scan(self, value:int):
       print(f"this is not value {value}")  


    def set_origin(self):
        #Resets NED Values to (0,0,0)
        self.setHome()


    def mission_one(self):
        self.takeoff()
        time.sleep(12)
        self.land()

    def mission_two(self):
        self.takeoff()
        time.sleep(12)
        self.approach()
        time.sleep(10)
        self.returns()
        time.sleep(10)
        self.land()




"""
app = QApplication(sys.argv)

window = AutonBeckDavid()
window.show()
app.exec()
"""