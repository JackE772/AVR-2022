import RPi.GPIO as GPIO
import itertools
import time

halfstep_seq = [
   [1,0,0,0],
   [1,1,0,0],
   [0,1,0,0],
   [0,1,1,0],
   [0,0,1,0],
   [0,0,1,1],
   [0,0,0,1],
   [1,0,0,1]
]

GPIO.setmode(GPIO.BOARD)
control_pins = [7,11,13,15]
control_pins_side = [32,36,38,40]
for pin in control_pins:
   GPIO.setup(pin, GPIO.OUT)
   GPIO.output(pin, 0)
for pin in control_pins_side:
   GPIO.setup(pin, GPIO.OUT)
   GPIO.output(pin, 0)


class gimbal:

   stepAngle = 0
   currentAngle = [0,0] # (y,x) don't ask
   limit = 45
   def __init__(self, stepAngle, limit) -> None:
      self.stepAngle = stepAngle
      self.limit = limit
      GPIO.setmode(GPIO.BOARD)
      #sets up the pins for output
      control_pins = [7,11,13,15]
      control_pins_side = [32,36,38,40]
      for pin in control_pins:
         GPIO.setup(pin, GPIO.OUT)
         GPIO.output(pin, 0)
      for pin in control_pins_side:
         GPIO.setup(pin, GPIO.OUT)
         GPIO.output(pin, 0)

   #controls all vertical movement using pins 7,11,13,15
   def verticalMove(self, steps, halfstep_seq) -> int:
      if(self.checkRangeY(steps)):
         for _, halfstep in itertools.product(range(steps), range(8)):#loops over steps(halfsteps(pins))
            for pin in range(4):
               GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)#delay here so that it works idk why it needs to be here
            for pin in range(4):
               GPIO.output(control_pins[pin], 0)
         return steps*self.stepAngle #outputs the angle change
      return 0

   #exactly the same as the vertical movment just with different pins (should probably only be one function with the pins as inputs)
   def HorazontalMove(self, steps, halfstep_seq) -> int:
      if(self.checkRangeY(steps)):
         for _, halfstep in itertools.product(range(steps), range(8)):
            for pin in range(4):
               GPIO.output(control_pins_side[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)
         for pin in range(4):
            GPIO.output(control_pins_side[pin], 0)
         return steps*self.stepAngle
      return 0
   #moves with defualt halfstep seq
   def moveUp(self, steps):
      halfstep_seq = [
         [1,0,0,0],
         [1,1,0,0],
         [0,1,0,0],
         [0,1,1,0],
         [0,0,1,0],
         [0,0,1,1],
         [0,0,0,1],
         [1,0,0,1]
      ]
      self.currentAngle[0] += self.verticalMove(steps, halfstep_seq)

   #I maunaly swaped the order of the halfsteps this is a bad way of writing it but im sick
   def moveDown(self, steps):
      halfstep_seq = [
         [1,0,0,1],
         [0,0,0,1],
         [0,0,1,1],
         [0,0,1,0],
         [0,1,1,0],
         [0,1,0,0],
         [1,1,0,0],
         [1,0,0,0]
      ]
      self.currentAngle[0] -= self.verticalMove(steps, halfstep_seq)

   def moveLeft(self, steps):
      halfstep_seq = [
         [1,0,0,1],
         [0,0,0,1],
         [0,0,1,1],
         [0,0,1,0],
         [0,1,1,0],
         [0,1,0,0],
         [1,1,0,0],
         [1,0,0,0]
      ]
      self.currentAngle[1] += self.HorazontalMove(steps, halfstep_seq)

   def moveRight(self, steps):
      halfstep_seq = [
         [1,0,0,0],
         [1,1,0,0],
         [0,1,0,0],
         [0,1,1,0],
         [0,0,1,0],
         [0,0,1,1],
         [0,0,0,1],
         [1,0,0,1]
      ]
      self.currentAngle[1] -= self.HorazontalMove(steps, halfstep_seq)

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

   #checks that the angle in any direction is not greater than the limit angle
   def checkRangeX(self, steps):
      return True
      if(steps * self.stepAngle + self.currentAngle[1] > self.limit):
         print("hit limit")
         return False
      elif(-1 * steps * self.stepAngle + self.currentAngle[1] >= self.limit):
         print("hit limit")
         return False
      return True


   def checkRangeY(self, steps):
      return True
      if(steps * self.stepAngle + self.currentAngle[0] > self.limit):
         print("hit limt")
         return False
      if( -1 * steps * self.stepAngle + self.currentAngle[0] >= self.limit):
         print("hit limit 1")
         return False
      return True

   def getCurrentY(self):
      return self.currentAngle[0]
   def getCurrentX(self):
      return self.currentAngle[1]

   def changeLimit(self, limit):
      self.limit = limit

   def setCurrentAngle(self, currentAngle):
      self.currentAngle = currentAngle




#setup = gimbal(1.417, 90) #DO NOT PASS GIMBAL 0 MOVE TO POS WILL NOT WORK

#scale = 1

#you get a warning if this is not run on shutdown still works without
GPIO.cleanup()
