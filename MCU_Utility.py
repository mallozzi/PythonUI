# Utility Functions relating to micro-controller
import math
import Hardware_Constants as HW


def calcDutyCycleInt(EField):
    # Converts a desired Electric Field in Volts/meter to a duty cycle integer
    # INPUTS
    # EField is the desired electric field in Volts/meter
    # OUTPUT
    # dutyCycleInt is the duty cycle integer that will be applied to achieve desired electric field.

    # Use regression fit from data to calculate duty cycle integer from desired electric field
    #dutyCycleInt = int(round(HW.DUTY_CYCLE_INTERCEPT + EField * HW.DUTY_CYCLE_SLOPE))
    dutyCycleInt = int(round(EField * HW.DUTY_CYCLE_SLOPE))

    return dutyCycleInt


def validatePulseParameters(paramsDictObj):
    # Validates the pulse parameters in the user interface with respect to limitations
    # INPUT
    # paramsDictObj is a dictionary object containing the values of the parameters. It comes from the property
    # __pulseParameters in the EFieldToroidApp class.
    # OUTPUT
    # isValid is boolean True if the parameters are valid, False if not
    # msg is a string message describing the error

        isValid = True
        msg = ''

        # Electric field amplitude
        EFieldAmp = paramsDictObj['EFieldAmp']
        EFieldLobeDuration = paramsDictObj['EFieldLobeDuration']

        if EFieldAmp > HW.EFIELD_MAX_POTENTIAL:
            isValid = False
            msg = 'E-Field exceeds maximum of ' + str(HW.EFIELD_MAX_POTENTIAL) + ' V/m'
        elif EFieldAmp*EFieldLobeDuration > HW.EFIELD_TIME_PROD_LIMIT:
            isValid = False
            allowableAmp = round(float(HW.EFIELD_TIME_PROD_LIMIT)/EFieldLobeDuration - 0.005, 2)  # round down to nearest one hundredth
            msg = 'E-Field amplitude exceeds allowable value for a ' + str(EFieldLobeDuration) + ' ms pulse. ' + \
                  'Maximum allowable amplitude for this pulse length is ' + str(allowableAmp) + ' V/m'

        interPulseSpacing = paramsDictObj['PulseSpacing']
        if interPulseSpacing > HW.PULSE_SPACING_MAX:
            isValid = False
            msg = 'Maximum Inter-Pulse Spacing is ' + str(HW.PULSE_SPACING_MAX) + ' ms.'
        elif interPulseSpacing < HW.PULSE_SPACING_MIN:
            isValid = False
            msg = 'Minimum Inter-Pulse Spacing is ' + str(HW.PULSE_SPACING_MIN) + ' ms.'

        return isValid, msg



