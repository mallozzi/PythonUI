# Contains constants pertinent to hardware and firmware for the micro-controller and the Beaglebone Black

# Micro-controller
# Regression fit that gives duty cycle integer as function of E Field in V/m. Formula is
# Duty Cycle Int = DUTY_CYCLE_INTERCEPT + DUTY_CYCLE_SLOPE * E. Note that 100% duty cycle corresponds to a duty cycle integer of 255
DUTY_CYCLE_INTERCEPT = 27.842
DUTY_CYCLE_SLOPE = 37.257

# Regression fit that gives the pre-bias integer as a function of E Field in V/m if auto-prebias is used. Formula is
# PREBIAS = PB_A0 + PB_A1 * E.
PB_A0 = 25
PB_A1 = 2.787

PULSE_SPACING_MAX = 65  # maximum pulse spacing allowable in ms. This is the time from the end of one pulse to the beginning of the next
PULSE_SPACING_MIN = 2  # minimum pulse spacing allowable in ms.
EFIELD_MAX_POTENTIAL = 6.1  # nominal value of electric field at 100% pwm duty cycle
EFIELD_TIME_PROD_LIMIT = 61  # limit of the product of the electric field in [V/m] and the duration of one lobe in ms
I2C_SLAVE_ADDRESS = 111  # slave address for micro-controller

# ******* I2C COMMUNICATION *************************************************************
# **** These definitions are implemented in the micro-controller code in the file *****
# **** registerHandler.c *****

# I2C Register Definitions
REG_COMMAND = 1  # register for issuing a command
REG_PULSE_AMP = 9  # pulse amplitude register
REG_PULSE_DURATION = 19  # pulse duration register
REG_PULSE_SPACING = 29  # inter-pulse spacing (end of last to beginning of next)
REG_PRE_BIAS = 39  # pre-bias pwm duty cycle value

# I2C Data definitions
START_PULSING = 1  # begin pulsing electric field
STOP_PULSING = 2   # stop pulsing electric field

# ******** END I2C COMMUNICATIONS ********************************************************

# Beaglebone Black
#...pin definitions
GLOBAL_ENABLE_PIN = "P9_23"
MCU_RESET_PIN = "P8_11"
ADC_CHAN1_PIN = "P9_40"
ADC_CHAN2_PIN = "P9_39"
ENABLE = 1 # for general use
DISABLE = 0 # for general use

#...ADC to current conversion factor. Multiply this by ADC value to get current. Beaglebone ADC gives a number 0-1.0, where 1.0 corresponds
#...to the max voltage of 1.8V
#ADC_CURRENT_CONVERSION = 2.51
ADC_CURRENT_CONVERSION = 4.14

#...Current Limit for safety
CURRENT_LIMIT = 2.0  # Amps