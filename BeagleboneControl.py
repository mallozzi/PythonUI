
import time
from Adafruit_GPIO import I2C as i2c
from Adafruit_BBIO import GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import Hardware_Constants as HW
import MCU_Utility as MCFuncs

#These lines are called upon import
#...initialize bus
i2cDev = i2c.Device(HW.I2C_SLAVE_ADDRESS,2) # bus 2 is the available i2c bus
#...ADC setup
ADC.setup()


def setRegisterValue(regNum, value):
    # Sends a data byte to specified register through i2c
    i2cDev.write16(regNum, value)
    mcuValue = readRegisterValue(regNum)
    valueVerified = (mcuValue == value)
    return valueVerified


def readRegisterValue(regNum):
    # Reads a 16-bit unsigned integer from a register through i2c
    val = i2cDev.readU16(regNum)
    return val


def sendPulseParametersToMCU(parametersDictObj):
    # Sends pulse parameters to the MCU and reads them back to make sure they are accurate
    # INPUT
    # paramsDictObj is a dictionary object containing the values of the parameters. It comes from the property
    # __pulseParameters in the EFieldToroidApp class.
    # OUTPUT
    # transmissionVerified is True if the read numbers match the transmitted, False otherwise

    transmissionVerified = True

    # DC-bias - this must be sent before the pulse amplitudes because they are computed relative to this in the MCU
    EFieldDCOffset = parametersDictObj['dcBias']
    dcOffsetDutyCycleInt = int(round(EFieldDCOffset * HW.DUTY_CYCLE_SLOPE))
    print 'DC bias value: ' + str(dcOffsetDutyCycleInt)
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_DC_BIAS, dcOffsetDutyCycleInt)
    time.sleep(.01)

    # Pulse Duration for positive lobe
    pulseDurPosInt = HW.TIMER1_CYC_PER_MS * parametersDictObj['EFieldLobeDurationPos']
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_POS_PULSE_DURATION, pulseDurPosInt)
    time.sleep(.01)

    # Pulse Duration for negative lobe
    pulseDurNegInt = HW.TIMER1_CYC_PER_MS * parametersDictObj['EFieldLobeDurationNeg']
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_NEG_PULSE_DURATION, pulseDurNegInt)
    time.sleep(.01)

    # Pulse Spacing
    pulseSpaceInt = HW.TIMER1_CYC_PER_MS * parametersDictObj['PulseSpacing']
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_PULSE_SPACING, pulseSpaceInt)
    time.sleep(.01)

    # Pulse amplitudes - must translate V/m to duty cycle integer
    valPos = parametersDictObj['EFieldAmpPos']
    dutyCycleInt = MCFuncs.calcDutyCycleInt(valPos)
    print 'EFieldAmpPos: Sending duty cycle integer of ' + str(dutyCycleInt)
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_POS_PULSE_AMP, dutyCycleInt)

    valNeg = parametersDictObj['EFieldAmpNeg']
    dutyCycleInt = MCFuncs.calcDutyCycleInt(valNeg)
    print 'EFieldAmpNeg: Sending duty cycle integer of ' + str(dutyCycleInt)
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_NEG_PULSE_AMP, dutyCycleInt)
    time.sleep(.01)

    return transmissionVerified


def startPulsing():
    time.sleep(0.01)
    setRegisterValue(HW.REG_COMMAND, HW.START_PULSING)
    time.sleep(.01)


def stopPulsing():
    # First set amplitude to zero for a few ms to let things de-energize
    setRegisterValue(HW.REG_POS_PULSE_AMP, 0)
    setRegisterValue(HW.REG_NEG_PULSE_AMP, 0)
    time.sleep(.05)
    setRegisterValue(HW.REG_COMMAND, HW.STOP_PULSING)
    time.sleep(.05)
    time.sleep(0.5)


def verifyRegisterWrite(regNum, sentValue):
    # verifies that a value written to MCU matches what it was supposed to be
    # INPUTS
    # regNum is the register number to check
    # sentValue is the value that was sent that should match what gets read
    # OUTPUT
    # isGood is True if the sent value matches the read value, False otherwise
    readVal = i2cDev.readU16(regNum)
    isGood = readVal == sentValue
    return isGood





