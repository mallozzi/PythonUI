# Utility Functions relating to micro-controller
import math
import Hardware_Constants as HW


def calcDutyCycleInt(EField):
    # Converts a desired Electric Field in Volts/meter to a duty cycle integer for positive or lobe of pulse
    # INPUTS
    # EField is a positive float giving the deviation of the desired electric field in Volts/meter from the dc value
    # OUTPUT
    # dutyCycleInt is the duty cycle integer that will be added or subtracted from the dc duty cycle to achieve desired electric field.

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

    # Electric field amplitude of positive lobe
    EFieldAmpPos = paramsDictObj['EFieldAmpPos'] + paramsDictObj['dcBias']

    # TO DO: enforce limits for pulse durations

    if EFieldAmpPos > HW.EFIELD_MAX_POTENTIAL:
        isValid = False
        msg = 'Peak E-Field of ' + str(EFieldAmpPos)+ 'V/m exceeds maximum of ' + str(HW.EFIELD_MAX_POTENTIAL) + ' V/m.'
    elif EFieldAmpPos < 0:
        isValid = False
        msg = 'Peak E-field must be a positive number'

    # Electric field amplitude of negative lobe
    EFieldAmpNeg = -paramsDictObj['EFieldAmpNeg'] + paramsDictObj['dcBias']
    if abs(EFieldAmpNeg) > HW.EFIELD_MAX_POTENTIAL:
        isValid = False
        msg = 'Minimum Negative E-Field of ' + str(EFieldAmpNeg)+ 'V/m is less than ' + str(-HW.EFIELD_MAX_POTENTIAL) + ' V/m.'

    # Pulse duration
    posPulseDuration = paramsDictObj['EFieldLobeDurationPos']
    if posPulseDuration > HW.PULSE_DURATION_MAX:
        isValid = False
        msg = 'Maximum pulse lobe duration is ' + str(HW.PULSE_SPACING_MAX) + ' ms'
    elif posPulseDuration < HW.PULSE_DURATION_MIN:
        isValid = False
        msg = 'Minimum pulse lobe duration is ' + str(HW.PULSE_SPACING_MIN) + ' ms'
    negPulseDuration = paramsDictObj['EFieldLobeDurationNeg']
    if negPulseDuration > HW.PULSE_DURATION_MAX:
        isValid = False
        msg = 'Maximum pulse lobe duration is ' + str(HW.PULSE_SPACING_MAX) + ' ms'
    elif negPulseDuration < HW.PULSE_DURATION_MIN:
        isValid = False
        msg = 'Minimum pulse lobe duration is ' + str(HW.PULSE_SPACING_MIN) + ' ms'

    interPulseSpacing = paramsDictObj['PulseSpacing']
    if interPulseSpacing > HW.PULSE_SPACING_MAX:
        isValid = False
        msg = 'Maximum Inter-Pulse Spacing is ' + str(HW.PULSE_SPACING_MAX) + ' ms.'
    elif interPulseSpacing < HW.PULSE_SPACING_MIN:
        isValid = False
        msg = 'Minimum Inter-Pulse Spacing is ' + str(HW.PULSE_SPACING_MIN) + ' ms.'

    return isValid, msg



