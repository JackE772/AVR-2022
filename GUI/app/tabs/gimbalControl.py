from typing import Literal
from .base import BaseTabWidget
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from enum import Enum, auto
import functools
from bell.avr.utils.timing import rate_limit
from typing import Optional, Tuple
from ..lib.config import config
from ..lib.calc import map_value

from bell.avr.mqtt.payloads import (
    AvrPcmStepperMovePayload,
    AvrPcmSetServoAbsPayload,
    AvrPcmSetServoOpenClosePayload,
)


class Direction(Enum):
    Left = auto()
    Right = auto()
    Up = auto()
    Down = auto()

class JoystickWidget(BaseTabWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setFixedSize(300, 300)

        self.moving_offset = QtCore.QPointF(0, 0)

        self.grab_center = False
        self.__max_distance = 100

        self.current_y = 0
        self.current_x = 0

        self.servoxmin = 10
        self.servoymin = 10
        self.servoxmax = 99
        self.servoymax = 99

        # gimbal declarations
        self.Gimbal_Min = 150 #number of steps accross
        self.Gimbal_Max = 0

        self.centerValue = self.Gimbal_Min // 2
        print(f"center at {self.centerValue}")
        self.netX = self.centerValue
        self.netY = self.centerValue


    def _center(self) -> QtCore.QPointF:
        """
        Return the center of the widget.
        """
        return QtCore.QPointF(self.width() / 2, self.height() / 2)



    def update_steppers(self) -> None:
        """
        Update the servos on joystick movement.
        """

        x_servo_abs = round(
            map_value(self.current_x + 25, 25, 225, self.Gimbal_Min, self.Gimbal_Max)
        )
        x_servo_abs = int(x_servo_abs)

        y_servo_abs = round(
            map_value(self.current_y, 25, 225, self.Gimbal_Min, self.Gimbal_Max)
        )
        y_servo_abs = int(y_servo_abs)

        x_move_value = self.netX + x_servo_abs
        y_move_value = self.netY + y_servo_abs

        if(x_move_value > self.centerValue):
            self.send_message(
                "avr/pcm/stepper/move",
                AvrPcmStepperMovePayload(steps=x_move_value, direction="L")
            )
        elif(x_move_value < self.centerValue):
            self.send_message(
                "avr/pcm/stepper/move",
                AvrPcmStepperMovePayload(steps=x_move_value, direction="R")
            )
        if(y_move_value > self.centerValue):
            self.send_message(
                "avr/pcm/stepper/move",
                AvrPcmStepperMovePayload(steps=y_move_value, direction="D")
            )
        elif(y_move_value < self.centerValue):
            self.send_message(
                "avr/pcm/stepper/move",
                AvrPcmStepperMovePayload(steps=y_move_value, direction="U")
            )
        self.netX = self.centerValue - x_servo_abs
        self.netY = self.centerValue - y_servo_abs



    def _center_ellipse(self) -> QtCore.QRectF:
        # sourcery skip: assign-if-exp
        if self.grab_center:
            center = self.moving_offset
        else:
            center = self._center()

        return QtCore.QRectF(-20, -20, 40, 40).translated(center)

    def _bound_joystick(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """
        If the joystick is leaving the widget, bound it to the edge of the widget.
        """
        if point.x() > (self._center().x() + self.__max_distance):
            point.setX(int(self._center().x() + self.__max_distance))
        elif point.x() < (self._center().x() - self.__max_distance):
            point.setX(int(self._center().x() - self.__max_distance))

        if point.y() > (self._center().y() + self.__max_distance):
            point.setY(int(self._center().y() + self.__max_distance))
        elif point.y() < (self._center().y() - self.__max_distance):
            point.setY(int(self._center().y() - self.__max_distance))
        return point

    def joystick_direction(self) -> Optional[Tuple[Direction, float]]:
        """
        Retrieve the direction the joystick is moving
        """
        if not self.grab_center:
            return None

        norm_vector = QtCore.QLineF(self._center(), self.moving_offset)
        current_distance = norm_vector.length()
        angle = norm_vector.angle()

        distance = min(current_distance / self.__max_distance, 1.0)

        if 45 <= angle < 135:
            return (Direction.Up, distance)
        elif 135 <= angle < 225:
            return (Direction.Left, distance)
        elif 225 <= angle < 315:
            return (Direction.Down, distance)

        return (Direction.Right, distance)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        bounds = QtCore.QRectF(
            -self.__max_distance,
            -self.__max_distance,
            self.__max_distance * 2,
            self.__max_distance * 2,
        ).translated(self._center())

        # painter.drawEllipse(bounds)
        painter.drawRect(bounds)
        painter.setBrush(QtCore.Qt.GlobalColor.black)

        painter.drawEllipse(self._center_ellipse())

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> QtGui.QMouseEvent:
        """
        On a mouse press, check if we've clicked on the center of the joystick.
        """
        self.grab_center = self._center_ellipse().contains(event.pos())
        return event

    def mouseReleaseEvent(self, event: QtCore.QEvent) -> None:
        # self.grab_center = False
        # self.moving_offset = QtCore.QPointF(0, 0)
        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.grab_center:
            self.moving_offset = self._bound_joystick(event.pos())
            self.update()

        moving_offset_y = self.moving_offset.y()
        if not config.joystick_inverted:
            moving_offset_y = self.height() - moving_offset_y

        # print(self.joystick_direction())
        self.current_x = (
            self.moving_offset.x() - self._center().x() + self.__max_distance
        )
        self.current_y = moving_offset_y - self._center().y() + self.__max_distance

        rate_limit(self.update_steppers, frequency=50)


class gimbalControlWidget(BaseTabWidget):

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("gimbal control")

        self.scale = 10
        self.largestScale = 50

    def build(self) ->None:
        """
        building the GUI
        """
        layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(layout)


        joystick_groupbox = QtWidgets.QGroupBox("Joystick")
        joystick_layout = QtWidgets.QVBoxLayout()
        joystick_groupbox.setLayout(joystick_layout)

        sub_joystick_layout = QtWidgets.QHBoxLayout()
        joystick_layout.addLayout(sub_joystick_layout)

        self.joystick = JoystickWidget(self)
        sub_joystick_layout.addWidget(self.joystick)
        self.joystick.emit_message.connect(self.emit_message.emit)

        layout.addWidget(joystick_groupbox)

        #layout of slider and buttons
        slider_button_groupbox = QtWidgets.QGroupBox()
        slider_button_layout = QtWidgets.QVBoxLayout()
        slider_button_groupbox.setLayout(slider_button_layout)

        #movement scale slider
        slider_groupbox = QtWidgets.QGroupBox("scale slider")
        slider_layout = QtWidgets.QHBoxLayout()
        slider_groupbox.setLayout(slider_layout)

        #adds slider to set scale of movement
        scale_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        scale_slider.setGeometry(50,50,200,50)
        scale_slider.setRange(1,self.largestScale)
        scale_slider.setSingleStep(self.largestScale/50)
        scale_slider.valueChanged.connect(lambda: self.setScale(scale_slider.value()))

        slider_layout.addWidget(scale_slider)
        slider_button_layout.addWidget(slider_groupbox)

        #makes the gimbal controler box
        button_groupbox = QtWidgets.QGroupBox("control buttons")
        button_layout = QtWidgets.QHBoxLayout()
        button_groupbox.setLayout(button_layout)

        left_button = QtWidgets.QPushButton("left")
        left_button.clicked.connect(lambda: self.controlStepper(self.scale, "L"))
        button_layout.addWidget(left_button)

        right_button = QtWidgets.QPushButton("right")
        right_button.clicked.connect(lambda: self.controlStepper(self.scale, "R"))
        button_layout.addWidget(right_button)

        down_button = QtWidgets.QPushButton("up")
        down_button.clicked.connect(lambda: self.controlStepper(self.scale, "D"))
        button_layout.addWidget(down_button)

        up_button = QtWidgets.QPushButton("down")
        up_button.clicked.connect(lambda: self.controlStepper(self.scale, "U"))
        button_layout.addWidget(up_button)

        slider_button_layout.addWidget(button_groupbox)
        layout.addWidget(slider_button_groupbox)

        holder_groupbox = QtWidgets.QGroupBox("")
        holder_layout = QtWidgets.QVBoxLayout()
        holder_groupbox.setLayout(holder_layout)

        auger_groupbox = QtWidgets.QGroupBox("auger controls")
        auger_layout = QtWidgets.QVBoxLayout()
        auger_groupbox.setLayout(auger_layout)

        auger_button = QtWidgets.QPushButton("drop")
        auger_button.clicked.connect(functools.partial(self.set_servo, 1, "open"))  # type: ignore
        auger_layout.addWidget(auger_button)

        auger_stop_button = QtWidgets.QPushButton("Seal")
        auger_stop_button.clicked.connect(functools.partial(self.set_servo, 1, "close"))
        auger_layout.addWidget(auger_stop_button)


        holder_layout.addWidget(auger_groupbox)

        servo_groupbox = QtWidgets.QGroupBox("Vacuum slider")
        servo_layout = QtWidgets.QHBoxLayout()
        servo_groupbox.setLayout(servo_layout)

        servo_1_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        servo_1_slider.setGeometry(50,50,200,50)
        servo_1_slider.setMinimum(100)
        servo_1_slider.setMaximum(200)
        servo_1_slider.setValue(86)
        servo_1_slider.valueChanged.connect(lambda: self.setSlider(servo_1_slider.value()))
        servo_layout.addWidget(servo_1_slider)

        servo_close_button = QtWidgets.QPushButton("Stop/Arm")
        servo_close_button.clicked.connect(functools.partial(self.set_servo_pos, 0, 2000, False)) #sets to fully on
        servo_layout.addWidget(servo_close_button)

        holder_layout.addWidget(servo_groupbox)

        layout.addWidget(holder_groupbox)

    def controlStepper(self, step:int, dir:str) ->None:
        self.send_message(
            "avr/pcm/stepper/move",
            AvrPcmStepperMovePayload(steps=step, direction=dir)
        )

    def setScale(self, value):
        self.scale = value
        print(f"current scale: {self.scale}")

    def setSlider(self, position:int) -> None:
        self.set_servo_pos(0, position*10, False)

    def set_servo_pos(self, number: int, position: int, map: bool) -> None:
        """
        Set a servo state
        """
        if(map):
            position = map_value(position, 0, 180,1000, 2000)
        self.send_message(
            "avr/pcm/set_servo_abs",
            AvrPcmSetServoAbsPayload(servo=number, absolute=position),
        )

    def set_servo(self, number: int, action: Literal["open", "close"]) -> None:
        """
        Set a servo state
        """
        self.send_message(
            "avr/pcm/set_servo_open_close",
            AvrPcmSetServoOpenClosePayload(servo=number, action=action),
        )
