
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
#...GPIO setup
GPIO.setup("P8_10", GPIO.IN)


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
    # ...inner rings
    EFieldDCOffset = parametersDictObj['dcBias']
    dcOffsetDutyCycleIntInner = int(round(EFieldDCOffset * HW.DUTY_CYCLE_SLOPE_INNER))
    print 'DC bias value for inner rings: ' + str(dcOffsetDutyCycleIntInner)
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_DC_BIAS_INNER, dcOffsetDutyCycleIntInner)
    time.sleep(.01)

    # ...outer rings
    EFieldDCOffset = parametersDictObj['dcBias']
    dcOffsetDutyCycleIntOuter = int(round(EFieldDCOffset * HW.DUTY_CYCLE_SLOPE_OUTER))
    print 'DC bias value for outer rings: ' + str(dcOffsetDutyCycleIntOuter)
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_DC_BIAS_OUTER, dcOffsetDutyCycleIntOuter)
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
    # ...inner rings positive lobe
    valPos = parametersDictObj['EFieldAmpPos']
    dutyCycleIntInner = MCFuncs.calcDutyCycleIntInner(valPos)
    print 'EFieldAmpPos: Sending duty cycle integer of ' + str(dutyCycleIntInner) + ' for inner rings positive lobe'
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_POS_PULSE_AMP_INNER, dutyCycleIntInner)

    # ...outer rings positive lobe
    valPos = parametersDictObj['EFieldAmpPos']
    dutyCycleIntOuter = MCFuncs.calcDutyCycleIntOuter(valPos)
    print 'EFieldAmpPos: Sending duty cycle integer of ' + str(dutyCycleIntOuter) + ' for outer rings positive lobe'
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_POS_PULSE_AMP_OUTER, dutyCycleIntOuter)

    # ...inner rings negative lobe
    valNeg = parametersDictObj['EFieldAmpNeg']
    dutyCycleIntInnerNeg = MCFuncs.calcDutyCycleIntInner(valNeg)
    print 'EFieldAmpNeg: Sending duty cycle integer of ' + str(dutyCycleIntInnerNeg) + ' for inner rings negative lobe'
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_NEG_PULSE_AMP_INNER, dutyCycleIntInnerNeg)
    time.sleep(.01)

    # ...outer rings negative lobe
    valNeg = parametersDictObj['EFieldAmpNeg']
    dutyCycleIntOuterNeg = MCFuncs.calcDutyCycleIntOuter(valNeg)
    print 'EFieldAmpNeg: Sending duty cycle integer of ' + str(dutyCycleIntOuterNeg) + ' for outer rings negative lobe'
    transmissionVerified = transmissionVerified and setRegisterValue(HW.REG_NEG_PULSE_AMP_OUTER, dutyCycleIntOuterNeg)
    time.sleep(.01)

    return transmissionVerified


def startPulsing():
    time.sleep(0.01)
    setRegisterValue(HW.REG_COMMAND, HW.START_PULSING)
    time.sleep(.01)


def stopPulsing():
    # First set amplitude to zero for a few ms to let things de-energize
    #setRegisterValue(HW.REG_POS_PULSE_AMP_INNER, 0)
    #setRegisterValue(HW.REG_POS_PULSE_AMP_OUTER, 0)
    #setRegisterValue(HW.REG_NEG_PULSE_AMP_INNER, 0)
    #setRegisterValue(HW.REG_NEG_PULSE_AMP_OUTER, 0)
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


def getErrorText(errorFlagByte):
    # Converts the error flag byte, which is an unsigned integer, to error text. This method documents the meanings, which must match those in the
    # MCU code.
    # INPUT
    # errorFlagByte is a single 16-bit unsigned integer with each bit representing an error flag
    # OUTPUT
    # errorTextList is a list of strings with error messages for each error bit that is set in the errorFlagByte input

    errorTextList = []
    for whichBit in range(0, 16):
        flagMask = 1 << whichBit
        if flagMask & errorFlagByte > 0:
            # bit is 1, retrieve associated error text. The definitions are stored in this segment of code, and must match those in the MCU code
            if whichBit == 0:
                errorTextList.append('V1+ coil pulse not detected')
            elif whichBit == 1:
                errorTextList.append('V1- coil pulse not detected')
            elif whichBit == 2:
                errorTextList.append('V2+ coil pulse not detected')
            elif whichBit == 3:
                errorTextList.append('V2- coil pulse not detected')

    return errorTextList


def checkForFaults():
    # Checks GPIO input for indication of fault on signal. Returns True if fault detected, False otherwise
    faultInput = GPIO.input("P8_10")
    if faultInput > 0:
        faultDetected = True
    else:
        faultDetected = False
    return faultDetected


def getErrorMessages():
    # Retrieves fault flag byte from MCU and returns a list of error messages.
    faultFlagByte = readRegisterValue(HW.REG_ERROR_FLAGS)
    print('faultFlagByte: ')
    print(faultFlagByte)
    errorMessageList = getErrorText(faultFlagByte)
    return errorMessageList



