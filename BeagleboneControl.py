
import time
from Adafruit_GPIO import I2C as i2c
from Adafruit_BBIO import GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import Hardware_Constants as HW
import MCU_Utility as MCFuncs

#These lines are called upon import
#...initialize bus
i2cDev = i2c.Device(HW.I2C_SLAVE_ADDRESS,2) # bus 2 is the available i2c bus
#...initialize GPIO output
GPIO.setup(HW.MCU_RESET_PIN,GPIO.OUT)
GPIO.output(HW.MCU_RESET_PIN,GPIO.LOW)
#...ADC setup
ADC.setup()


def setRegisterValue(regNum, value):
    # Sends a data byte to specified register through i2c
    i2cDev.write16(regNum, value)


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

    # Pulse Duration
    pulseDurInt = HW.TIMER1_CYC_PER_MS * parametersDictObj['EFieldLobeDuration']
    setRegisterValue(HW.REG_PULSE_DURATION, pulseDurInt)
    transmissionVerified = transmissionVerified and verifyRegisterWrite(HW.REG_PULSE_DURATION, pulseDurInt)
    time.sleep(.01)

    # Pulse Spacing
    pulseSpaceInt = HW.TIMER1_CYC_PER_MS * parametersDictObj['PulseSpacing']
    setRegisterValue(HW.REG_PULSE_SPACING, pulseSpaceInt)
    transmissionVerified = transmissionVerified and verifyRegisterWrite(HW.REG_PULSE_SPACING, pulseSpaceInt)
    time.sleep(.01)

    # Pulse amplitude - must translate V/m to duty cycle integer
    val = parametersDictObj['EFieldAmp']
    dutyCycleInt = MCFuncs.calcDutyCycleInt(val)
    print 'Sending duty cycle integer of ' + str(dutyCycleInt)
    setRegisterValue(HW.REG_POS_PULSE_AMP, dutyCycleInt)
    transmissionVerified = transmissionVerified and verifyRegisterWrite(HW.REG_POS_PULSE_AMP, dutyCycleInt)
    setRegisterValue(HW.REG_NEG_PULSE_AMP, dutyCycleInt)
    transmissionVerified = transmissionVerified and verifyRegisterWrite(HW.REG_NEG_PULSE_AMP, dutyCycleInt)
    time.sleep(.01)

    # Pre-bias
    print 'Pre-bias value: ' + str(parametersDictObj['preBias'])
    setRegisterValue(HW.REG_PRE_BIAS, parametersDictObj['preBias'])
    transmissionVerified = transmissionVerified and verifyRegisterWrite(HW.REG_PRE_BIAS, parametersDictObj['preBias'])
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
    resetMCU()  # This is a kluge to avoid some sort of glitch
    time.sleep(0.5)


def resetMCU():
    GPIO.output(HW.MCU_RESET_PIN, GPIO.HIGH)
    time.sleep(0.02)
    GPIO.output(HW.MCU_RESET_PIN, GPIO.LOW)


def readCurrent(duration_ms):
    # Reads the current from the ADC for each channel and returns the result in Amps
    # INPUT
    # duration_ms is the duration to poll the current in ms
    # OUTPUTS
    # current1 and current2 is the current in Amps in each channel

    duration = float(duration_ms)/1000
    done = False
    max_adc1 = 0.0;
    max_adc2 = 0.0;
    startTime = time.time()
    while not done:
        adc1 = ADC.read(HW.ADC_CHAN1_PIN)
        adc2 = ADC.read(HW.ADC_CHAN2_PIN)
        max_adc1 = max(max_adc1, adc1)
        max_adc2 = max(max_adc2, adc2)
        tm = time.time()-startTime
        if tm > duration:
            done = True

    current1 = max_adc1 * HW.ADC_CURRENT_CONVERSION
    current2 = max_adc2 * HW.ADC_CURRENT_CONVERSION
    return current1, current2


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





