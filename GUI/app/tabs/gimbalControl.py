from typing import List, Optional, Tuple, Literal
from .base import BaseTabWidget
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from enum import Enum, auto
import functools
from bell.avr.utils.timing import rate_limit
from typing import Optional, Tuple
from ..lib.config import config
import colour
from ..lib.calc import map_value
from pynput import keyboard
import math

from bell.avr.mqtt.payloads import (
    AvrPcmStepperMovePayload,
    AvrPcmSetServoAbsPayload,
    AvrPcmSetServoOpenClosePayload,
    AvrPcmSetServoPctPayload,
    AvrPcmSetLaserOnPayload,
    AvrPcmSetLaserOffPayload,
)


class Direction(Enum):
    Left = auto()
    Right = auto()
    Up = auto()
    Down = auto()


"""
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
        #Return the center of the widget.
"""
        return QtCore.QPointF(self.width() / 2, self.height() / 2)



    def update_steppers(self) -> None:
        """
        #Update the servos on joystick movement.
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
        #If the joystick is leaving the widget, bound it to the edge of the widget.
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
        #Retrieve the direction the joystick is moving
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
        #On a mouse press, check if we've clicked on the center of the joystick.
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
"""

class ThermalView(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        # canvas size
        self.width_ = 300
        self.height_ = self.width_

        # pixels within canvas
        self.pixels_x = 30
        self.pixels_y = self.pixels_x

        self.pixel_width = self.width_ / self.pixels_x
        self.pixel_height = self.height_ / self.pixels_y

        # low range of the sensor (this will be blue on the screen)
        self.MINTEMP = 20.0

        # high range of the sensor (this will be red on the screen)
        self.MAXTEMP = 32.0

        # last lowest temp from camera
        self.last_lowest_temp = 999.0

        # how many color values we can have
        self.COLORDEPTH = 1024

        # how many pixels the camera is
        self.camera_x = 8
        self.camera_y = self.camera_x
        self.camera_total = self.camera_x * self.camera_y

        # create list of x/y points
        self.points = [
            (math.floor(ix / self.camera_x), (ix % self.camera_y))
            for ix in range(self.camera_total)
        ]
        # i'm not fully sure what this does
        self.grid_x, self.grid_y = np.mgrid[
            0 : self.camera_x - 1 : self.camera_total / 2j,
            0 : self.camera_y - 1 : self.camera_total / 2j,
        ]

        # create avaiable colors
        self.colors = [
            (int(c.red * 255), int(c.green * 255), int(c.blue * 255))
            for c in list(
                colour.Color("indigo").range_to(colour.Color("red"), self.COLORDEPTH)
            )
        ]

        # create canvas
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.canvas = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.canvas)
        self.view.setGeometry(0, 0, self.width_, self.height_)

        layout.addWidget(self.view)

        # need a bit of padding for the edges of the canvas
        self.setFixedSize(self.width_ + 50, self.height_ + 50)

    def set_temp_range(self, mintemp: float, maxtemp: float) -> None:
        self.MINTEMP = mintemp
        self.MAXTEMP = maxtemp

    def set_calibrted_temp_range(self) -> None:
        self.MINTEMP = self.last_lowest_temp + 0.0
        self.MAXTEMP = self.last_lowest_temp + 15.0

    def update_canvas(self, pixels: List[int]) -> None:
        float_pixels = [
            map_value(p, self.MINTEMP, self.MAXTEMP, 0, self.COLORDEPTH - 1)
            for p in pixels
        ]

        # Rotate 90° to orient for mounting correctly
        float_pixels_matrix = np.reshape(float_pixels, (self.camera_x, self.camera_y))
        float_pixels_matrix = np.rot90(float_pixels_matrix, 1)
        rotated_float_pixels = float_pixels_matrix.flatten()

        bicubic = scipy.interpolate.griddata(
            self.points,
            rotated_float_pixels,
            (self.grid_x, self.grid_y),
            method="cubic",
        )

        pen = QtGui.QPen(QtCore.Qt.PenStyle.NoPen)
        self.canvas.clear()

        for ix, row in enumerate(bicubic):
            for jx, pixel in enumerate(row):
                brush = QtGui.QBrush(
                    QtGui.QColor(
                        *self.colors[int(constrain(pixel, 0, self.COLORDEPTH - 1))]
                    )
                )
                self.canvas.addRect(
                    self.pixel_width * jx,
                    self.pixel_height * ix,
                    self.pixel_width,
                    self.pixel_height,
                    pen,
                    brush,
                )


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

        # servo declarations
        self.SERVO_ABS_MAX = 2200
        self.SERVO_ABS_MIN = 700

    def _center(self) -> QtCore.QPointF:
        """
        Return the center of the widget.
        """
        return QtCore.QPointF(self.width() / 2, self.height() / 2)

    def move_gimbal(self, x_servo_percent: int, y_servo_percent: int) -> None:
        self.send_message(
            "avr/pcm/set_servo_pct",
            AvrPcmSetServoPctPayload(servo=2, percent=x_servo_percent),
        )
        self.send_message(
            "avr/pcm/set_servo_pct",
            AvrPcmSetServoPctPayload(servo=3, percent=y_servo_percent),
        )

    def move_gimbal_absolute(self, x_servo_abs: int, y_servo_abs: int) -> None:
        self.send_message(
            "avr/pcm/set_servo_abs",
            AvrPcmSetServoAbsPayload(servo=2, absolute=x_servo_abs),
        )
        self.send_message(
            "avr/pcm/set_servo_abs",
            AvrPcmSetServoAbsPayload(servo=3, absolute=y_servo_abs),
        )

    def update_servos(self) -> None:
        """
        Update the servos on joystick movement.
        """
        # y_reversed = 100 - self.current_y

        # x_servo_percent = round(map_value(self.current_x, 0, 100, 10, 99))
        # y_servo_percent = round(map_value(y_reversed, 0, 100, 10, 99))
        #
        # if x_servo_percent < self.servoxmin:
        #     return
        # if y_servo_percent < self.servoymin:
        #     return
        # if x_servo_percent > self.servoxmax:
        #     return
        # if y_servo_percent > self.servoymax:
        #     return
        #
        # self.move_gimbal(x_servo_percent, y_servo_percent)

        y_reversed = 225 - self.current_y
        # side to side  270 left, 360 right

        x_servo_abs = round(
            map_value(
                self.current_x + 25, 25, 225, self.SERVO_ABS_MIN, self.SERVO_ABS_MAX
            )
        )
        y_servo_abs = round(
            map_value(y_reversed, 25, 225, self.SERVO_ABS_MIN, self.SERVO_ABS_MAX)
        )

        self.move_gimbal_absolute(x_servo_abs, y_servo_abs)

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

        rate_limit(self.update_servos, frequency=50)


class gimbalControlWidget(BaseTabWidget):

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("gimbal control")

        self.scale = 10
        self.largestScale = 50

        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()  # start to listen on a separate thread
        #listener.join()  # remove if main thread is polling self.keys

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
        #layout.addWidget(slider_button_groupbox)

        servo_groupbox = QtWidgets.QGroupBox("Vacuum slider")
        servo_layout = QtWidgets.QVBoxLayout()
        servo_groupbox.setLayout(servo_layout)

        servo_close_button = QtWidgets.QPushButton("Stop/Arm")
        servo_close_button.clicked.connect(functools.partial(self.set_servo_pos, 0, 2000, False)) #sets to fully on
        servo_layout.addWidget(servo_close_button)

        laser_on_button = QtWidgets.QPushButton("laser on")
        servo_layout.addWidget(laser_on_button)

        laser_off_button = QtWidgets.QPushButton("laser off")
        servo_layout.addWidget(laser_off_button)

        laser_on_button.clicked.connect(lambda: self.set_laser(True))  # type: ignore
        laser_off_button.clicked.connect(lambda: self.set_laser(False))  # type: ignore

        layout.addWidget(servo_groupbox)

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

    def on_press(self, key):
        try:
            #dont judge the if else list because its dogshit code
            k = key.char  # single-char keys
            if k == "q":  #seal
                self.set_servo_pos(1, 2000, False)
            elif k == "w": #open
                self.set_servo_pos(1, 400, False)
            elif k == "y": #swing arm
                self.set_servo_pos(4, 800, False)
            elif k == "u": #swing arm halfway to mid
                self.set_servo_pos(4, 1000, False)
            elif k == "i": #swing arm to middle
                self.set_servo_pos(4, 1400, False)
            elif k == "o": #swing arm halfway to end
                self.set_servo_pos(4, 1600, False)
            elif k == "p": #swing arm to end
                self.set_servo_pos(4, 1800, False)
            elif k == "0":
                self.set_servo_pos(0, 1000, False)
            elif k == "1":
                self.set_servo_pos(0, 1200, False)
            elif k == "2":
                self.set_servo_pos(0, 1400, False)
            elif k == "3":
                self.set_servo_pos(0, 1600, False)
            elif k == "4":
                self.set_servo_pos(0, 1800, False)
            elif k == "5":
                self.set_servo_pos(0, 2000, False)
        except Exception:
            print("key not found")

    def set_laser(self, state: bool) -> None:
        if state:
            topic = "avr/pcm/set_laser_on"
            payload = AvrPcmSetLaserOnPayload()
            text = "Laser On"
            color = "green"
        else:
            topic = "avr/pcm/set_laser_off"
            payload = AvrPcmSetLaserOffPayload()
            text = "Laser Off"
            color = "red"

        self.send_message(topic, payload)
        self.laser_toggle_label.setText(wrap_text(text, color))
