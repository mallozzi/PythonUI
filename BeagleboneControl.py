
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
    i2cDev.write8(regNum, value)


def init_GlobalEnable():
    # Initializes the Global Enable digital output pin
    GPIO.setup(HW.GLOBAL_ENABLE_PIN, GPIO.OUT)


def setGlobalEnable(val):
    # Enables or Disables system
    # INPUTS
    # val is set to 1 (ENABLE) to enable the system, 0 (DISABLE) to disable

    if val == HW.DISABLE:
        GPIO.output(HW.GLOBAL_ENABLE_PIN, GPIO.LOW)
    if val == HW.ENABLE:
        GPIO.output(HW.GLOBAL_ENABLE_PIN, GPIO.HIGH)


def sendPulseParametersToMCU(parametersDictObj):
    # Sends pulse parameters to the MCU
    # INPUT
    # paramsDictObj is a dictionary object containing the values of the parameters. It comes from the property
    # __pulseParameters in the EFieldToroidApp class.

    setRegisterValue(HW.REG_PULSE_DURATION, parametersDictObj['EFieldLobeDuration'])
    time.sleep(.01)

    setRegisterValue(HW.REG_PULSE_SPACING,parametersDictObj['PulseSpacing'])
    time.sleep(.01)

    # Pulse amplitude - must translate V/m to duty cycle integer
    val = parametersDictObj['EFieldAmp']
    dutyCycleInt = MCFuncs.calcDutyCycleInt(val)
    print 'Sending duty cycle integer of ' + str(dutyCycleInt)
    setRegisterValue(HW.REG_PULSE_AMP, dutyCycleInt)
    time.sleep(.01)

    # Pre-bias
    print 'Pre-bias value: ' + str(parametersDictObj['preBias'])
    setRegisterValue(HW.REG_PRE_BIAS, parametersDictObj['preBias'])
    time.sleep(.01)


def startPulsing():
    time.sleep(0.01)
    setRegisterValue(HW.REG_COMMAND, HW.START_PULSING)
    time.sleep(.01)


def stopPulsing():
    # First set amplitude to zero for a few ms to let things de-energize
    setRegisterValue(HW.REG_PULSE_AMP, 0)
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







