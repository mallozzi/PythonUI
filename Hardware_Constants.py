# Contains constants pertinent to hardware and firmware for the micro-controller and the Beaglebone Black

# Current version is for dsPic33CH512MP508


DUTY_CYCLE_SLOPE_INNER = 4.387          # Change in PWM duty cycle integer in MCU for each V/m change in E Field
DUTY_CYCLE_SLOPE_OUTER = 14.75          # Change in PWM duty cycle integer in MCU for each V/m change in E Field


PULSE_SPACING_MAX = 250         # maximum pulse spacing allowable in ms. This is the time from the end of one pulse to the beginning of the next. A setting of 250
                                # assumes a 128 MHz clock frequency (64 MHz instruction cycle), with a Timer1 prescale divider of 256, for a 16-bit timer.
PULSE_SPACING_MIN = 2           # minimum pulse spacing allowable in ms.
EFIELD_MAX_POTENTIAL = 40       # nominal value of electric field at 100% pwm duty cycle
PULSE_DURATION_MAX = 250        # maximum duration of either positive or negative lobe
PULSE_DURATION_MIN = 1          # minimum duration of either positive or negative lobe


# MICROCONTROLLER INFO
I2C_SLAVE_ADDRESS = 111         # slave address for micro-controller
TIMER1_CYC_PER_MS = 250         # 128 MHz osc freq, Timer1 prescaler of 256, 2 osc cycles per instruction cycle.


# I2C Register Definitions
REG_COMMAND = 1                 # register for issuing a command
REG_POS_PULSE_AMP_INNER = 9     # pulse amplitude register for positive lobe on inner ring set
REG_POS_PULSE_AMP_OUTER = 8     # pulse amplitude register for positive lobe on outer ring set
REG_NEG_PULSE_AMP_INNER = 10    # pulse amplitude for negative lobe
REG_NEG_PULSE_AMP_OUTER = 11    # pulse amplitude for negative lobe
REG_POS_PULSE_DURATION = 18     # pulse duration register
REG_NEG_PULSE_DURATION = 19
REG_PULSE_SPACING = 29          # inter-pulse spacing (end of last to beginning of next)
REG_DC_BIAS_INNER = 39          # DC bias pwm duty cycle value for inner rings
REG_DC_BIAS_OUTER = 38          # DC bias pwm duty cycle value for outer rings
REG_ZERO_OUTPUT = 37            # pwm integer that leads to zero output
REG_ERROR_FLAGS = 40            # access error flags byte

# I2C Data definitions
START_PULSING = 1               # begin pulsing electric field
STOP_PULSING = 2                # stop pulsing electric field

# Fault States


