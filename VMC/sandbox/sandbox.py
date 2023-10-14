# Here we import our own MQTT library which takes care of a lot of boilerplate
# code related to connecting to the MQTT server and sending/receiving messages.
# It also helps us make sure that our code is sending the proper payload on a topic
# and is receiving the proper payload as well.
from bell.avr.mqtt.client import MQTTModule
from bell.avr.mqtt.payloads import AvrFcmVelocityPayload, AvrPcmStepperMovePayload

# This imports the third-party Loguru library which helps make logging way easier
# and more useful.
# https://loguru.readthedocs.io/en/stable/
from loguru import logger
#libs needed to run steppers 
import Jetson.GPIO as GPIO
import itertools
import time


#gimbal for the laser
class gimbal:

   stepAngle = 0
   halfstep_seq_frw = [
         [1,0,0,0],
         [1,1,0,0],
         [0,1,0,0],
         [0,1,1,0],
         [0,0,1,0],
         [0,0,1,1],
         [0,0,0,1],
         [1,0,0,1]
    ]
   halfstep_seq_bck = [
         [1,0,0,1],
         [0,0,0,1],
         [0,0,1,1],
         [0,0,1,0],
         [0,1,1,0],
         [0,1,0,0],
         [1,1,0,0],
         [1,0,0,0]
    ]
   def __init__(self, stepAngle) -> None:
      self.stepAngle = stepAngle
      GPIO.setmode(GPIO.BOARD)
      #sets up the pins for output
      self.control_pins = [7,11,13,15]
      self.control_pins_side = [32,36,38,40]
      for pin in self.control_pins:
         GPIO.setup(pin, GPIO.OUT)
         GPIO.output(pin, 0)
      for pin in self.control_pins_side:
         GPIO.setup(pin, GPIO.OUT)
         GPIO.output(pin, 0)

   def move(self, steps:int, direction:str): #steps:the number of full steps direction:"L-R-U-D"
         for _, halfstep in itertools.product(range(steps), range(8)):#loops over steps(halfsteps(pins))
            if(direction == "R"):
                  for pin in range(4):
                     if(self.halfstep_seq_frw[halfstep][pin] == 1):
                           GPIO.output(self.control_pins[pin], GPIO.HIGH)
                     else:
                           GPIO.output(self.control_pins[pin], GPIO.LOW)
                  time.sleep(0.001)#delay here so that it works
            elif(direction == "U"):
                  for pin in range(4):
                     if(self.halfstep_seq_frw[halfstep][pin] == 1):
                           GPIO.output(self.control_pins_side[pin], GPIO.HIGH)
                     else:
                           GPIO.output(self.control_pins_side[pin], GPIO.LOW)
                  time.sleep(0.001)#delay here so that it works
            elif(direction == "L"):
                  for pin in range(4):
                     if(self.halfstep_seq_bck[halfstep][pin] == 1):
                           GPIO.output(self.control_pins_side[pin], GPIO.HIGH)
                     else:
                           GPIO.output(self.control_pins_side[pin], GPIO.LOW)
                  time.sleep(0.001)#delay here so that it works
            elif(direction == "D"):
                  for pin in range(4):
                     if(self.halfstep_seq_bck[halfstep][pin] == 1):
                           GPIO.output(self.control_pins_side[pin], GPIO.HIGH)
                     else:
                           GPIO.output(self.control_pins_side[pin], GPIO.LOW)
                  time.sleep(0.001)#delay here so that it works
            else:
               logger.debug(f"ERROR no valid direction passed {direction} was passed must be U,D,L,R")
         for pin in range(4):
            GPIO.output(self.control_pins[pin], GPIO.LOW)
            GPIO.output(self.control_pins_side[pin], GPIO.LOW)

   def getCurrentY(self):
      return self.currentAngle[0]
   def getCurrentX(self):
      return self.currentAngle[1]

   def changeLimit(self, limit):
      self.limit = limit

   def setCurrentAngle(self, currentAngle):
      self.currentAngle = currentAngle

   #tested and kinda works rn but the angle dosnt seem to be that great
   def moveBy_X_Y(self, x, y):
      #converts from str to int
      x = int(x) #target position X
      y = int(y) #target position Y

      difY = self.currentAngle[0] + y #differance between target and current
      difX = self.currentAngle[1] + x
      print(difX)
      print(int(difX/self.stepAngle))
      if(difX < 0):
         self.moveRight(int(difX/self.stepAngle))
      elif(difX > 0):
         self.moveLeft(int(difX/self.stepAngle))

      if(difY < 0):
         self.moveDown(int(difY/self.stepAngle))
      elif(difY > 0):
         self.moveUp(int(difY/self.stepAngle))

      #self.currentAngle = [y + self.currentAngle[0], x + self.currentAngle[1]]

   def getCurrentY(self):
      return self.currentAngle[0]
   def getCurrentX(self):
      return self.currentAngle[1]

   def changeLimit(self, limit):
      self.limit = limit

   def setCurrentAngle(self, currentAngle):
      self.currentAngle = currentAngle


# This creates a new class that will contain multiple functions
# which are known as "methods". This inherits from the MQTTModule class
# that we imported from our custom MQTT library.
class Sandbox(MQTTModule):
    # The "__init__" method of any class is special in Python. It's what runs when
    # you create a class like `sandbox = Sandbox()`. In here, we usually put
    # first-time initialization and setup code. The "self" argument is a magic
    # argument that must be the first argument in any class method. This allows the code
    # inside the method to access class information.
    def __init__(self) -> None:
        # This calls the original `__init__()` method of the MQTTModule class.
        # This runs some setup code that we still want to occur, even though
        # we're replacing the `__init__()` method.
        super().__init__()
        #makes the gimbal object so that we can call the movment functions
        self.laser_gimbal = gimbal(1.77)
        # Here, we're creating a dictionary of MQTT topic names to method handles.
        # A dictionary is a data structure that allows use to
        # obtain values based on keys. Think of a dictionary of state names as keys
        # and their capitals as values. By using the state name as a key, you can easily
        # find the associated capital. However, this does not work in reverse. So here,
        # we're creating a dictionary of MQTT topics, and the methods we want to run
        # whenever a message arrives on that topic.
        self.topic_map = {"avr/fcm/velocity": self.show_velocity}
        self.topic_map["avr/pcm/stepper/move"] = self.show_stepper

    # Here's an example of a custom message handler here.
    # This is what executes whenever a message is received on the "avr/fcm/velocity"
    # topic. The content of the message is passed to the `payload` argument.
    # The `AvrFcmVelocityMessage` class here is beyond the scope of AVR.
    def show_velocity(self, payload: AvrFcmVelocityPayload) -> None:
        vx = payload["vX"]
        vy = payload["vY"]
        vz = payload["vZ"]
        v_ms = (vx, vy, vz)

        # Use methods like `debug`, `info`, `success`, `warning`, `error`, and
        # `critical` to log data that you can see while your code runs.

        # This is what is known as a "f-string". This allows you to easily inject
        # variables into a string without needing to combine lots of strings together.
        # https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python
        logger.debug(f"Velocity information: {v_ms} m/s")
    
    def show_stepper(self, payload: AvrPcmStepperMovePayload) -> None:
        steps = payload["steps"]
        steps = int(steps)
        direction = payload["direction"]
        logger.debug(f"steps: {steps} direction {direction}")
        self.laser_gimbal.move(steps, direction)

    # Here is an example on how to publish a message to an MQTT topic to
    # perform an action
    def open_servo(self) -> None:
        # It's super easy, use the `self.send_message` method with the first argument
        # as the topic, and the second argument as the payload.
        # Pro-tip, if you set `python.analysis.typeCheckingMode` to `basic` in you
        # VS Code preferences, you'll get a red underline if your payload doesn't
        # match the expected format for the topic.
        self.send_message(
            "avr/pcm/set_servo_open_close",
            {"servo": 0, "action": "open"},
        )


if __name__ == "__main__":
    # This is what actually initializes the Sandbox class, and executes it.
    # This is nested under the above condition, as otherwise, if this file
    # were imported by another file, these lines would execute, as the interpreter
    # reads and executes the file top-down. However, whenever a file is called directly
    # with `python file.py`, the magic `__name__` variable is set to "__main__".
    # Thus, this code will only execute if the file is called directly.
    box = Sandbox()
    # The `run` method is defined by the inherited `MQTTModule` class and is a
    # convience function to start processing incoming MQTT messages infinitely.
    box.run()
