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


def sendPulseParametersToMCU(parametersDictObj):
    verifiedTransmission = True
    return verifiedTransmission


def startPulsing():
    dummy = 1


def stopPulsing():
    dummy = 1


def checkForFaults():
    # Checks GPIO input for indication of fault on signal. Simulator just returns a 'no fault detected' signal
    return False


def getErrorMessages():
    # Retrieves fault flag byte from MCU and returns a list of error messages.
    errorMessageList = ['simulation: no error messages']
    return errorMessageList
