from .base import BaseTabWidget
from PySide6 import QtCore, QtGui, QtWidgets

from bell.avr.mqtt.payloads import AvrPcmStepperMovePayload

class gimbalControlWidget(BaseTabWidget):

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("gimbal control")

    def build(self) ->None:
        """
        building the GUI
        """
        layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(layout)

        #makes the gimbal controler
        button_groupbox = QtWidgets.QGroupBox("control buttons")
        button_layout = QtWidgets.QVBoxLayout()
        button_groupbox.setLayout(button_layout)

        left_button = QtWidgets.QPushButton("left")
        left_button.clicked.connect(lambda: self.controlStepper(1, "L"))
        button_layout.addWidget(left_button)


        layout.addWidget(button_groupbox)

    def controlStepper(self, step:int, dir:str) ->None:
        self.send_message(
            "avr/pcm/stepper/move",
            AvrPcmStepperMovePayload(steps=step, direction=dir)
        )