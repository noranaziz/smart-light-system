import aiocoap.resource as resource
import aiocoap
import asyncio
import RPi.GPIO as GPIO
from datetime import datetime
import board
import neopixel
import colorsys
from gpiozero import MotionSensor
import time

# sets up GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# IR receiver setup
pin = 17
GPIO.setup(pin, GPIO.IN)

# PIR motion sensor setup
pir = MotionSensor(4)
motion = False
detect_motion = False

# RGB LED setup
redPin = 10
greenPin = 9
bluePin = 11
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)

# LED strip setup
pixels1 = neopixel.NeoPixel(board.D21, 30, brightness=1)
R = 255
G = 255
B = 255
brightness = 1
power = False
rgb = False
speed = 0.15
rgb_task = None

# stepper motor setup
in1 = 26
in2 = 19
in3 = 13
in4 = 6

step_count = 1000 # 5.625*(1/64) per step, 4096 steps is 360°

step_sequence = [[1,0,0,1],
                 [1,0,0,0],
                 [1,1,0,0],
                 [0,1,0,0],
                 [0,1,1,0],
                 [0,0,1,0],
                 [0,0,1,1],
                 [0,0,0,1]]

GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)

GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)

motor_pins = [in1,in2,in3,in4]
motor_step_counter = 0
direct = "down"

# variable for IR receiver
buttons = [
    [0x361a0f00f, "power", b"power"],     # 0
    [0x361a018e7, "ok", b"rgb"],          # 1
    [0x361a042bd, "up", b"red"],          # 2
    [0x361a0c23d, "down", b"white"],     # 3
    [0x361a06897, "left", b"green"],      # 4
    [0x361a0a857, "right", b"blue"],      # 5
    [0x361a030cf, "volume up", b"+"],     # 6
    [0x361a0b04f, "volume down", b"-"],   # 7
    [0x361a0708f, "mute", b"motion"],     # 8
    [0x361a0d827, "slow", b"slow"],       # 9
    [0x361a028d7, "speed", b"speed"]      # 10
]

#
# CoAP server resources
#

class HelloWorldResource(resource.Resource): # hello resource
    async def render_get(self, request): # method to handle GET requests for the resource
        print('GET: hello')
        return aiocoap.Message(payload = "hello world".encode()) # return the resource content as a response

class PowerResource(resource.Resource): # power resource
    global power # respond with the current power status (if the light is on or off)

    async def render_get(self, request): # method to handle GET requests for the resource
        print('GET: power ' + str(power))
        return aiocoap.Message(payload = str(power).encode()) # return the resource content as a response

class RemoteResource(resource.Resource): # remote resource
    def __init__(self):
        super().__init__()
        self.set_content(b"color")

    def set_content(self, content):
        self.content = content

    async def render_get(self, request): # method to handle GET requests for the resource
        return aiocoap.Message(payload=self.content)

    async def render_put(self, request): # method to handle PUT requests for the resource
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)
        await setColor(request.payload) # do the function based on the PUT request
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)

#
# IR receiver functions
#

async def getBinary():
    num1s = 0  # number of consecutive 1s read
    binary = 1  # the binary value
    command = []  # list to store pulse times in
    previousValue = 0  # the last value
    value = GPIO.input(pin)  # the current value

    # waits for the sensor to pull pin low
    while value:
        await asyncio.sleep(0.0001)
        value = GPIO.input(pin)
        
    # records start time
    startTime = datetime.now()
    
    while True:
        # if change detected in value
        if previousValue != value:
            now = datetime.now()
            pulseTime = now - startTime # calculate the time of pulse
            startTime = now # reset start time
            command.append((previousValue, pulseTime.microseconds)) # store recorded data
            
        # updates consecutive 1s variable
        if value:
            num1s += 1
        else:
            num1s = 0
        
        # breaks program when the amount of 1s surpasses 10000
        if num1s > 10000:
            break
            
        # re-reads pin
        previousValue = value
        value = GPIO.input(pin)
        
    # converts times to binary
    for (typ, tme) in command:
        if typ == 1: # if looking at rest period
            if tme > 1000: # if pulse greater than 1000us
                binary = binary *10 +1 # must be 1
            else:
                binary *= 10 # must be 0
            
    if len(str(binary)) > 34: # fixes stray characters that may occur
        binary = int(str(binary)[:34])
        
    return binary
    
def convertHex(binaryValue):
    tmpB2 = int(str(binaryValue),2)
    return hex(tmpB2)

#
# PIR motion sensor functions
#

async def checkMotion():
    global motion
    global power
    global detect_motion
    prev_motion = False

    while True:
        if detect_motion == True:
            if pir.value == 1:
                motion = True
            elif pir.value == 0:
                motion = False

            if motion != prev_motion: # check if there is a change in motion state
                if motion:
                    if power == False:
                        await setColor(b"on")
                    print("motion detected")
                else:
                    await setColor(b"off")
                    print("motion stopped")
                prev_motion = motion

        await asyncio.sleep(0.1)

#
# stepper motor functions
#

async def moveMotor(direction):
    global motor_pins
    global motor_step_counter
    global step_sequence
    global step_count

    i = 0
    for i in range(step_count):
        for motor_pin in range(0, len(motor_pins)):
            GPIO.output(motor_pins[motor_pin], step_sequence[motor_step_counter][motor_pin])
        if direction == "down":
            motor_step_counter = (motor_step_counter - 1) % 8
        elif direction == "up":
            motor_step_counter = (motor_step_counter + 1) % 8
        else: 
            print("moveMotor received incorrect input")
        await asyncio.sleep(0.001)

#
# miscellaneous functions
#

async def setColor(color):
    global brightness
    global power
    global detect_motion
    global R
    global G
    global B
    global rgb
    global speed
    global rgb_task
    global direct

    if color != b"power" and color != b"off": # turn on the LED strip if other buttons are pressed so you don't have to turn it on with the power button every time
        power = True

    if color != b"rgb" and color != b"speed" and color != b"slow" and color != b"+" and color != b"-": # only stop rgb if anything other than these buttons are pressed
        rgb = False

    if color == b"power":
        # toggling power when power button pressed
        power = not power
        if power == True:
            if direct == "down":
                await moveMotor("up")
                direct = "up"
            brightness = 1
            GPIO.output(redPin,GPIO.HIGH)
            GPIO.output(greenPin,GPIO.HIGH)
            GPIO.output(bluePin,GPIO.HIGH)

        elif power == False:
            if direct == "up":
                await moveMotor("down")
                direct = "down"
            brightness = 0
            GPIO.output(redPin,GPIO.LOW)
            GPIO.output(greenPin,GPIO.LOW)
            GPIO.output(bluePin,GPIO.LOW)

    elif color == b"on":
        if direct == "down":
            await moveMotor("up")
            direct = "up"
        power = True
        brightness = 1
        GPIO.output(redPin,GPIO.HIGH)
        GPIO.output(greenPin,GPIO.HIGH)
        GPIO.output(bluePin,GPIO.HIGH)

    elif color == b"off":
        if direct == "up":
            await moveMotor("down")
            direct = "down"
        power = False
        brightness = 0
        GPIO.output(redPin,GPIO.LOW)
        GPIO.output(greenPin,GPIO.LOW)
        GPIO.output(bluePin,GPIO.LOW)

    elif color == b"motion":
        detect_motion = not detect_motion # toggle motion detection

    elif color == b"red":
        R = 255
        G = 0
        B = 0
        GPIO.output(redPin,GPIO.HIGH)
        GPIO.output(greenPin,GPIO.LOW)
        GPIO.output(bluePin,GPIO.LOW)

    elif color == b"green":
        R = 0
        G = 255
        B = 0
        GPIO.output(redPin,GPIO.LOW)
        GPIO.output(greenPin,GPIO.HIGH)
        GPIO.output(bluePin,GPIO.LOW)

    elif color == b"blue":
        R = 0
        G = 0
        B = 255
        GPIO.output(redPin,GPIO.LOW)
        GPIO.output(greenPin,GPIO.LOW)
        GPIO.output(bluePin,GPIO.HIGH)

    elif color == b"white":
        R = 255
        G = 255
        B = 255
        GPIO.output(redPin,GPIO.HIGH)
        GPIO.output(greenPin,GPIO.HIGH)
        GPIO.output(bluePin,GPIO.HIGH)

    elif color == b"yellow":
        R = 255
        G = 255
        B = 0
        GPIO.output(redPin,GPIO.HIGH)
        GPIO.output(greenPin,GPIO.HIGH)
        GPIO.output(bluePin,GPIO.LOW)

    elif color == b"rgb":
        GPIO.output(redPin,GPIO.HIGH)
        GPIO.output(greenPin,GPIO.HIGH)
        GPIO.output(bluePin,GPIO.HIGH)
        rgb = True
        if rgb_task is None or rgb_task.done():  # check if task is not running
            rgb_task = asyncio.create_task(runRgbTransition())
        else:
            print("RGB transition already running")

    elif color == b"+":
        brightness += 0.1

    elif color == b"-":
        brightness -= 0.1

    elif color == b"speed":
        speed -= 0.1

    elif color == b"slow":
        speed += 0.1

    else:
        print("command not found")

    # keep brightness value within range
    if brightness > 1:
        brightness = 1
    elif brightness < 0:
        brightness = 0

    # keep speed value within range
    if speed > 1.2:
        speed = 1.2
    elif speed < 0.05:
        speed = 0.05

    pixels1.fill((R * brightness, G * brightness, B * brightness))

async def runRgbTransition():
    global speed
    global rgb
    global brightness

    # smoothly transition through the RGB color spectrum
    while rgb == True:
        for hue in range(360):  # hue ranges from 0 to 359 (360 degrees)
            rgb_color = colorsys.hsv_to_rgb(hue / 360.0, 1.0, brightness)  # convert hue to RGB color
            neo_color = tuple(int(x * 255) for x in rgb_color)  # convert float RGB values to integers
            pixels1.fill(neo_color)
            await asyncio.sleep(0.05 * speed)  # adjust the speed of the transition

#
# main function
#

async def main():
    asyncio.create_task(checkMotion()) # checks the motion sensor asynchronously

    while True:
        # resource tree creation
        root = resource.Site()
        root.add_resource(['hello'], HelloWorldResource())
        root.add_resource(['remote'], RemoteResource())
        root.add_resource(['power'], PowerResource())

        await aiocoap.Context.create_server_context(root, bind=('10.25.3.27', 5683)) # creating CoAP server from RaspberryPi on port 5683

        inData = convertHex(await getBinary()) # receiving data from IR receiver
        
        for button in range(len(buttons)): # look for corresponding button from data received
            if hex(buttons[button][0]) == inData:
                if (rgb_task is not None and not rgb_task.done()) and (buttons[button][2] != b"speed" 
                        and buttons[button][2] != b"slow" and buttons[button][2] != b"+" and buttons[button][2] != b"-"):  # check if RGB task is running
                    rgb_task.cancel()  # cancel RGB transition if running
                await setColor(buttons[button][2])
                print(buttons[button][1])

if __name__ == "__main__":
    asyncio.run(main())
