# This file is for simulation purposes when running the UI in an environmment that does not have the Adafruit
# libraries installed. It presents the same interface as the BeagleboneControl.py file, but without any implementation.

# from Adafruit_GPIO import I2C as i2c
# from Adafruit_BBIO import GPIO as GPIO

#initialize bus
# i2cDev = i2c.Device(I2C_SLAVE_ADDRESS,2) # bus 2 is the available i2c bus


def setRegisterValue(regNum, value):
    # Sends a data byte to specified register through i2c
    # i2cDev.write8(regNum, value)
    dummy = True
    return dummy


def init_GlobalEnable():
    # Initializes the Global Enable digital output pin
    # GPIO.setup(HW.GLOBAL_ENABLE_PIN, GPIO.OUT)

    dummy = 1



def sendPulseParametersToMCU(parametersDictObj):
    verifiedTransmission = True
    return verifiedTransmission


def startPulsing():
    dummy = 1


def stopPulsing():
    dummy = 1

def resetMCU():
    dummy = 1

def readCurrent(duration_ms):
    return 0.123456, 0.2345678
