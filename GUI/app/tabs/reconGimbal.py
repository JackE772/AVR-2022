from PySide6 import QtWidgets, QtCore, QtGui
from .base import BaseTabWidget
import pygame
import math
import time

from bell.avr.mqtt.payloads import (
    AvrPcmStepperMovePayload,
    AvrPcmSetServoAbsPayload,
    AvrPcmSetServoOpenClosePayload,
    AvrPcmSetServoPctPayload,
    AvrPcmSetLaserOnPayload,
    AvrPcmSetLaserOffPayload,
)

# This is the UI box on the list of tabls
class ReconUIWidget(BaseTabWidget):
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("Recon")

    def build(self) ->None:
        """Add the layout components"""

        # outer box
        layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(layout)

        # inner box
        recon_groupbox = QtWidgets.QGroupBox("Recon Controller")
        recon_layout = QtWidgets.QVBoxLayout()
        recon_groupbox.setLayout(recon_layout)

        # recon widget in the inner box
        self.recon = ReconController(self)
        recon_layout.addWidget(self.recon)
        self.recon.emit_message.connect(self.emit_message.emit)

        layout.addWidget(recon_groupbox)




# This is the logic of the controller that is on the base tab
class ReconController(BaseTabWidget):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.init_pygame()
        self.initUI()
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_joystick_state)
        self.timer.start(5)  # Update every 5 ms
        # define the sensitivty needed for the controller
        self.settings = Settings()
        # define the gimbal mount object to be used to track and issue commands
        self.gimbalMount = GimbalMount(self.settings)
        # simple text variable for logging commands on screen
        self.commandLog = ""

    def init_pygame(self):
        pygame.init()
        pygame.joystick.init()
        self.joystick_count = pygame.joystick.get_count()
        if self.joystick_count > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        else:
            self.joystick = None

    def initUI(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.stateLabel = QtWidgets.QLabel("Joystick State: Not Connected", self)
        self.layout.addWidget(self.stateLabel)
        self.commandX = QtWidgets.QLabel("No Commands Issued", self)
        self.layout.addWidget(self.commandX)
        self.commandY = QtWidgets.QLabel("No Commands Issued", self)
        self.layout.addWidget(self.commandY)

    def update_joystick_state(self):
        if self.joystick:
            pygame.event.pump()  # Process event queue
            axis = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
            hats = [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]
            text = f"Axes: {axis}, Buttons: {buttons}, Hats: {hats}"

            # issue MQTT commands based on the movement of the axis
            self.process_axis(axis)

            # issue MTQQ commands based on the movement of the buttons
            self.process_buttons(buttons)

        else:
            text = "Joystick State: Not Connected"

        # show axis positions on screen
        self.stateLabel.setText(text)

    def build(self):
        # Any additional build steps can be added here
        pass

    def closeEvent(self, event: QtGui.QCloseEvent):
        pygame.quit()
        super().closeEvent(event)

    def scatter(self, pattern):
        for item in pattern:
            self.motion = item
            # move the servos
            self.gimbalMount.move_gimbal(self.motion)
            # check to see if mqtt movement commands are needed
            self.send_mqtt_move_commands()
            time.sleep(0.1)

    def process_buttons(self, buttons):
        """reserved for future use"""
        #scatter shot button mapped to the A button
        scale = 20
        if (buttons[0] == 1): #A button pressed
            #array of scatter shot offsets(PWM)
            scatterPaternA = [[scale,scale], [-2 * scale, 0], [0, -2*scale], [2*scale, 0], [-1* scale, scale]] #box pattern
            self.scatter(scatterPaternA)
        if(buttons[1] == 1): #B button pressed
            scale += 1
        if(buttons[2] == 1):
            scale -= 1

    def process_axis(self, axis):
        """move the gimbals based on axis movement"""
        self.motion = [0,0]
        # check for movement outside of the deadzone
        if(abs(axis[0]) > self.settings.deadzone):
            self.motion[0] = axis[0] * self.settings.sensitivityGross
        if(abs(axis[1]) > self.settings.deadzone):
            self.motion[1] = axis[1] * self.settings.sensitivityGross
        if(abs(axis[2]) > self.settings.deadzone):
            self.motion[0] = axis[2] * self.settings.sensitivityFine
        if(abs(axis[3]) > self.settings.deadzone):
           self.motion[1] = axis[3] * self.settings.sensitivityFine


        # move the servos
        self.gimbalMount.move_gimbal(self.motion)

        # check to see if mqtt movement commands are needed
        self.send_mqtt_move_commands()


    def send_mqtt_move_commands(self):

        # get the servo move. It comes in the form of a list in the following format
        # [(Move X?, Absolute Pulse), (Move Y?, Absolute Pulse)]
        self.servoMotion = self.gimbalMount.get_servo_move()


        # If servo 0 must move, the 0/0 position will be true
        if (self.servoMotion[0][0] == True):
            self.send_message(
                "avr/pcm/set_servo_abs",
                AvrPcmSetServoAbsPayload(servo=self.settings.ServoPinX, absolute=math.floor(self.servoMotion[0][1])),
            )
            self.commandLogX = f"Servo:{str(self.settings.ServoPinX)} set to {str(self.servoMotion[0][1])}/n"
            self.commandX.setText(self.commandLogX)

        # If servo 1 must move, the 1/0 position will be true
        if (self.servoMotion[1][0] == True):
            self.send_message(
                "avr/pcm/set_servo_abs",
                AvrPcmSetServoAbsPayload(servo=self.settings.ServoPinY, absolute=math.floor(self.servoMotion[1][1])),
            )
            self.commandLogY = f"Servo:{str(self.settings.ServoPinY)} set to {str(self.servoMotion[1][1])}/n"
            self.commandY.setText(self.commandLogY)


class GimbalMount:
    def __init__(self, settings):
        """Bind the X/Y servo motors and center them"""
        self.settings = settings
        self.servoX = Servo(settings.servoCenterX, settings.maxTravelX)
        self.servoY = Servo(settings.servoCenterY, settings.maxTravelY)
        self.moveX = False
        self.moveY = False


    def move_gimbal(self, motion):
        """pass the motion to the servos"""
        self.moveX = self.servoX.move_servo(motion[0])
        self.moveY = self.servoY.move_servo(motion[1])
        #print("Y servo moving by " + str(motion[1]))

    def get_servo_move(self):
        """returns a list [X,Y] with a tuple element in each (need to move? T/F, servo position)"""
        return [(self.moveX, self.servoX.position), (self.moveY, self.servoY.position)]

    def get_gimbal_position(self):
        return (self.servoX.position, self.servoY.position)



class Servo:

    def __init__(self, center, maxTravel):
        self.center = center
        self.maxTravel = maxTravel
        self.position = self.center


    def set_center(self):
        """moves the gimbal to the center"""
        self.position = self.center

    def move_servo(self, singleMotion):
        """moves the servo to the new position"""
        self.position += singleMotion

        # boundary condition check. Set to boundary if needed
        self.position = min(self.position, self.center + self.maxTravel)
        self.position = max(self.position, self.center - self.maxTravel)
        # notify gimbal mount if there is a new position
        return abs(singleMotion) > 0


class Settings:
    """simple object that has all the configuration settings"""
    def __init__(self):
        # microsecond pulse for the center for each servo
        self.servoCenterX = 1300
        self.servoCenterY = 1300

        # microsecond pulse difference between center and max travel allowed
        self.maxTravelX = 500
        self.maxTravelY = 500

        # multiplier for travel quickly (gross) and slowly (fine)
        self.sensitivityGross = 5
        self.sensitivityFine = 2

        # dead zone (ignore) in joystick
        self.deadzone = .06

        # number of the X Servo Pin
        self.ServoPinX = 2

        # number of the Y Servo Pin
        self.ServoPinY = 3