# NOTE - THIS CODE USES PYTHON 2.7.13
import sys
from PyQt4 import QtCore, QtGui, uic

import MCU_Utility as MCFuncs
import Hardware_Constants as HW
import csv
import os.path
import math
import json

import BeagleboneControl as BBB
#import BeagleboneSimulate as BBB

# --------------------------------

# Below is the line that needs to be changed depending upon the name of the
# output file from Qt Designer. It is the xml .ui file.

qtCreatorFile = "UI_MainWindow.ui"  # Enter file here.
qtAdvancedConfigDlg = "UI_AdvancedConfig.ui"
# --------------------------------

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
Ui_AdvancedConfigDlg, Ui_AdvancedConfigBaseClass = uic.loadUiType(qtAdvancedConfigDlg)

# Global Constants
ON = 1
OFF = 0


class MyApp(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Advanced Config Dialog
        self._advancedConfigDlg = AdvancedConfigDlg()

        # Properties
        self.__pulseParams = {'EFieldAmpPos': 0.5, 'EFieldAmpNeg': 0.5, 'PulseSpacing': 20, 'EFieldLobeDurationPos': 10, 'EFieldLobeDurationNeg': 10, 'dcBias': 1027}
        self._nonPulseParameters = {'IntervalOnTime': .3, 'IntervalOffTime': .2, 'MainTimer': 14, 'useTimerCB': True, 'useIntervalTimerCB': False, 'zeroAdjust': 1031}
        self._globalPulsingState = OFF  # either ON or OFF, depending on whether we are in pulsing mode. Note that we may be in an 'off' pulsing interval state,
                                        # but be in an ON global pulsing state. Being paused is also considered ON for the globalPulsingState

        # initialization
        pxmp = QtGui.QPixmap('OLogo.jpg')
        self.lbl_Logo.setPixmap(pxmp)

        self.__mv_gif = QtGui.QMovie('7SUb.gif')
        self.__mv_gif.setCacheMode(QtGui.QMovie.CacheAll)
        self.lbl_gif.setMovie(self.__mv_gif)
        self.__mv_gif.start()
        self.__mv_gif.stop()
        self.__mv_gif.jumpToFrame(1)

        # Fault Detection timer
        self._faultCheckTimer = QtCore.QTimer()
        self._faultCheckTimer.timeout.connect(self.checkForFaults)


        # Timer for pulsing duration for user
        self.__timer = QtCore.QTimer()
        self.__timer.timeout.connect(self.advanceTimer)
        self.__timerVal = 0
        self.__timerInitVal = 0  # initial value of timer (not current value)
        self.__timerUsed = False
        self.__timerExpired = False

        # Interval timer
        # The same interval timer is used for both ON and OFF state, which is tracked through the _intervalTimerPulseState property. The timer is set to one
        # second and calls the advanceIntervalTimer() method to update the display. The actual time on the timer is kept in _intervalTimerVal.
        self._intervalTimerUsed = False
        self._intervalTimerPulseState = OFF                 # determines whether pulsing is on or off (rest state) while interval pulsing is occurring
        self._intervalTimer = QtCore.QTimer()               # the actual timer object for the interval timer, used for both ON and OFF states.
        self._intervalTimer.timeout.connect(self.advanceIntervalTimer)
        self._intervalTimerVal = 0                          # The actual value on the timer in seconds
        self._intervalTimerInitVal = 0                      # initial value of timer (not current value)
        self._intervalTimerExpired = False

        # Pulsing pause state
        self._pulsingPaused = False
        self.pB_Pause.setEnabled(False)

        # SIGNALS for callback functions
        self.txEd_EFieldAmpPos.editingFinished.connect(self.EFieldAmpPosTextEdited)
        self.txEd_EFieldAmpNeg.editingFinished.connect(self.EFieldAmpNegTextEdited)
        self.txEd_pulseDurationPos.editingFinished.connect(self.pulseDurationPosTextEdited)
        self.txEd_pulseDurationNeg.editingFinished.connect(self.pulseDurationNegTextEdited)
        self.txEd_pulseSpacing.editingFinished.connect(self.pulseSpacingTextEdited)
        self.txEd_timerMin.editingFinished.connect(self.timerValTextEdited)
        self.pB_StartPulsing.clicked.connect(self.startPulsing)
        self.pB_StopPulsing.clicked.connect(self.stopPulsing)
        self.pB_Pause.clicked.connect(self.pausePulsing)
        self.pB_Verify.clicked.connect(self.verifyPulseParams)
        self.pB_ResetTimer.clicked.connect(self.resetTimer)
        self.pB_advancedConfig.clicked.connect(self.advancedConfigPB)
        self.act_Store_Default_Parameters.triggered.connect(self.storeDefaultParameters)
        self.act_Load_Default_Parameters.triggered.connect(self.loadDefaultParameters)
        self.act_Save_Protocol.triggered.connect(self.saveProtocol)
        self.act_Load_Protocol.triggered.connect(self.loadProtocol)
        self.cB_UseTimer.stateChanged.connect(self.timerStateChanged)
        self.cB_useIntervalMode.stateChanged.connect(self.intervalStateChanged)
        self.lnEd_onTime.editingFinished.connect(self.intervalTimerOnMinTextEdited)
        self.lnEd_offTime.editingFinished.connect(self.intervalTimerOffMinTextEdited)
        self.txEd_dcBias.editingFinished.connect(self.dcBiasTextEdited)
        self.txEd_zeroAdjust.editingFinished.connect(self.zeroAdjustTextEdited)

        # Load parameters from file
        self.loadDefaultParameters()

# *************  CALLBACKS  *************************

    def EFieldAmpPosTextEdited(self):
        value, valueText, valid = self._scrubNumericalInput(self.txEd_EFieldAmpPos, 2)
        inputInRange = validateParameter(value, 0.0, HW.EFIELD_MAX_POTENTIAL)
        if not inputInRange:
            self.txEd_EFieldAmpPos.setText(str(self.__pulseParams['EFieldAmpPos']))
            self.showMessageBox('Electric field must be between 0 and ' + str(HW.EFIELD_MAX_POTENTIAL) + ' V/m')

    def EFieldAmpNegTextEdited(self):
        value, valueText, valid = self._scrubNumericalInput(self.txEd_EFieldAmpNeg, 2)
        inputInRange = validateParameter(value, 0.0, HW.EFIELD_MAX_POTENTIAL)
        if not inputInRange:
            self.txEd_EFieldAmpNeg.setText(str(self.__pulseParams['EFieldAmpNeg']))
            self.showMessageBox('Electric field must be between 0 and ' + str(HW.EFIELD_MAX_POTENTIAL) + ' V/m')

    def pulseDurationPosTextEdited(self):
        self._scrubNumericalInput(self.txEd_pulseDurationPos, 0)

    def pulseDurationNegTextEdited(self):
        self._scrubNumericalInput(self.txEd_pulseDurationNeg, 0)

    def pulseSpacingTextEdited(self):
        self._scrubNumericalInput(self.txEd_pulseSpacing, 0)

    def timerValTextEdited(self):
        self._scrubNumericalInput(self.txEd_timerMin, 0)

    def intervalTimerOnMinTextEdited(self):
        self._scrubNumericalInput(self.lnEd_onTime, 1)

    def intervalTimerOffMinTextEdited(self):
        self._scrubNumericalInput(self.lnEd_offTime, 1)

    def dcBiasTextEdited(self):
        val, valstring, valid = self._scrubNumericalInput(self.txEd_dcBias, 1)
        if valid and val < 0:
            self.txEd_dcBias.setText(str(self.__pulseParams['dcBias']))
            self.showMessageBox('DC Bias must be greater than or equal to zero', 'User Input Error')

    def zeroAdjustTextEdited(self):
        value, strng, inputValid = self._scrubNumericalInput(self.txEd_zeroAdjust, 0)
        # this parameter must be sent to microcontroller immediately because it is a reference point for pulse parameters
        if inputValid:      # make sure input is valid first
            transmissionVerified = BBB.setRegisterValue(HW.REG_ZERO_OUTPUT, value)
            if not transmissionVerified:
                self.showMessageBox('Error Transmitting zero adjust value of i2c bus', 'ERROR')
        else:
            self.txEd_zeroAdjust.setText(str(self._nonPulseParameters['zeroAdjust']))

    def startPulsing(self):
        isValid, msg = self.verifyPulseParams()  # loads all parameters from UI too
        if isValid:
            self._globalPulsingState = ON
            if self.cB_UseTimer.isChecked():
                self.__timerInitVal = self._nonPulseParameters['MainTimer']  # number of minutes
                self.__timerVal = self.__timerInitVal*60  # seconds
                self.__timer.start(1000)  # update every second
                self.__timerUsed = True
                self.__timerExpired = False
            else:
                self.__timerInitVal = 0
                self.__timerUsed = False
                self.__timerVal = 0
                self.__timer.start(1000)  # update every second
            # Interval timer
            if self.cB_useIntervalMode.isChecked():
                self._intervalTimerUsed = True
                self.startIntervalTimer(ON)

            self.lbl_CountDown.setText(self.makeTimerString(self.__timerVal))
            transmissionVerified = BBB.sendPulseParametersToMCU(self.__pulseParams)
            if not transmissionVerified:
                self.showMessageBox('Error Transmitting Pulse Parameters over i2c bus', 'ERROR')
            BBB.startPulsing()
            self.DisableControls()
            self.pB_Pause.setEnabled(True)
            self._faultCheckTimer.start(2000)       # check every two seconds
            self.__mv_gif.start()

    def pausePulsing(self):
        # Pause or unpause pulsing
        if not self._pulsingPaused:
            self._intervalTimer.stop()
            self.__timer.stop()
            self._faultCheckTimer.stop()
            self.__mv_gif.stop()
            BBB.stopPulsing()
            self._pulsingPaused = True
            self.pB_Pause.setText('Continue Pulsing')
        else:
            self.__timer.start()
            self.__mv_gif.start()
            if self._intervalTimerUsed:
                self._intervalTimer.start()

            BBB.startPulsing()
            self._pulsingPaused = False
            self.pB_Pause.setText('Pause Pulsing')
            self._faultCheckTimer.start(2000)

    def startIntervalTimer(self, whichState):
        if self._globalPulsingState == ON:
            self._intervalTimerPulseState = whichState
            self._intervalTimerInitVal = self.getIntervalTimerInitVal(whichState)
            self._intervalTimerVal = self._intervalTimerInitVal * 60  # seconds
            self._intervalTimerExpired = False
            self._intervalTimer.start(1000)  # update every second
            self.lbl_intervalTime.setText(self.makeTimerString(self._intervalTimerVal))
            self.lbl_intervalState.setText('Pulsing')

    def stopIntervalTimer(self):
        self._intervalTimer.stop()
        self._intervalTimerPulseState = OFF
        self.lbl_intervalTime.setText(self.makeTimerString(0))
        self.lbl_intervalState.setText('')

    def getIntervalTimerInitVal(self, whichState):
        # Retrieves the initial value of the interval timer, for either the on or off state, from the user interface
        # INPUT
        # whichState should be ON to retrieve the timer setting for the ON state, and OFF for the timer value for the OFF state.
        # OUTPUT
        # timerValMin is the (float) value of the timer in minutes
        if whichState == ON:
            timerValMin = float(str(self.lnEd_onTime.text()))
        elif whichState == OFF:
            timerValMin = float(str(self.lnEd_offTime.text()))
        else:
            raise(ValueError('Error: whichState input should be either ON or OFF'))

        return timerValMin

    def stopPulsing(self):
        self._globalPulsingState = OFF
        BBB.stopPulsing()
        self.__timer.stop()
        self.__mv_gif.stop()
        self.__mv_gif.jumpToFrame(1)
        self.pB_Verify.setFocus()
        self.EnableControls()
        self.pB_Pause.setEnabled(False)
        self.pB_Pause.setText('Pause Pulsing')
        self.stopIntervalTimer()
        self._faultCheckTimer.stop()
        if self.__timerUsed and self.__timerExpired:
            self.showMessageBox('Pulsing Terminated After '+str(self.__timerInitVal)+ ' minutes','Info')

    def verifyPulseParams(self):
        self.loadPulseParamsFromUI()
        isValid, msg = MCFuncs.validatePulseParameters(self.__pulseParams)
        if not isValid:
            self.showMessageBox(msg, 'Invalid Parameter')

        return isValid, msg

    def storeDefaultParameters(self):
        # Stores a default parameter set, which gets loaded up when the software is started.
        self.loadPulseParamsFromUI()
        dictObj = self.makeParametersDictObj()

        with open('StoredParameters.txt', 'w+') as fp:
            json.dump(dictObj, fp, indent=4)
        self.showMessageBox('Parameters have been stored', 'Info')

    def loadDefaultParameters(self):
        if os.path.isfile('StoredParameters.txt'):
            with open('StoredParameters.txt', 'r') as fp:
                dictObj = json.load(fp)

            self.unpackParametersDictObj(dictObj)

    def saveProtocol(self):
        fileAndPathName = str(os.path.join(os.path.curdir,'Protocols'))
        protocolFilename = QtGui.QFileDialog.getSaveFileName(self, 'Store Protocol', fileAndPathName, '*.json')

        self.loadPulseParamsFromUI()
        dictObj = self.makeParametersDictObj()

        if not protocolFilename.isEmpty():
            with open(protocolFilename, 'w+') as fp:
                json.dump(dictObj, fp, indent=4)
            self.showMessageBox('Parameters have been stored', 'Info')

    def loadProtocol(self):
        protocolPathname = os.path.join(os.path.curdir,'Protocols')
        protocolFilename = QtGui.QFileDialog.getOpenFileName(self, 'Load Protocol', protocolPathname, '*.json')
        if not protocolFilename.isEmpty():
            with open(protocolFilename, 'r') as fp:
                dictObj = json.load(fp)
            self.unpackParametersDictObj(dictObj)

    def timerStateChanged(self):
        if self.cB_UseTimer.isChecked():
            enabledState = True
        else:
            enabledState = False
        self.txEd_timerMin.setEnabled(enabledState)
        self.lbl_Minutes.setEnabled(enabledState)

    def intervalStateChanged(self):
        if self.cB_useIntervalMode.isChecked():
            enabledState = True
        else:
            enabledState = False
        self.lnEd_onTime.setEnabled(enabledState)
        self.lnEd_offTime.setEnabled(enabledState)
        self.lbl_onTimeMin.setEnabled(enabledState)
        self.lbl_offTimeMin.setEnabled(enabledState)

    def resetTimer(self):
        self.lbl_CountDown.setText(self.makeTimerString(self.__timerInitVal*60))

    def checkForFaults(self):
        if not self._advancedConfigDlg.cB_disableFaultWarnings.isChecked():
            faultDetected = BBB.checkForFaults()
            #faultDetected = True
            if faultDetected:
                errorMessages = BBB.getErrorMessages()      # list object
                msgText = ['Error: The following fault(s) were detected: '] + errorMessages
                msgText.append('\n Note: Fault Detection can be disabled in the Advanced Configurations dialog')
                self.stopPulsing()
                self.showMessageBox(msgText)

    def advancedConfigPB(self):
        self._advancedConfigDlg.show()
        self._advancedConfigDlg.activateWindow()        # brings window back on top in case it got behind main window

# *************  NON-CALLBACK METHODS ***************

    def loadPulseParamsFromUI(self):
        self.__pulseParams['EFieldAmpPos'] = float(str(self.txEd_EFieldAmpPos.text()))
        self.__pulseParams['EFieldAmpNeg'] = float(str(self.txEd_EFieldAmpNeg.text()))
        self.__pulseParams['EFieldLobeDurationPos'] = int(round(float(str(self.txEd_pulseDurationPos.text()))))
        self.__pulseParams['EFieldLobeDurationNeg'] = int(round(float(str(self.txEd_pulseDurationNeg.text()))))
        self.__pulseParams['PulseSpacing'] = int(round(float(str(self.txEd_pulseSpacing.text()))))
        self.__pulseParams['dcBias'] = float(str(self.txEd_dcBias.text()))

        self._nonPulseParameters['IntervalOnTime'] = float(str(self.lnEd_onTime.text()))
        self._nonPulseParameters['IntervalOffTime'] = float(str(self.lnEd_offTime.text()))
        self._nonPulseParameters['MainTimer'] = int(str(self.txEd_timerMin.text()))
        self._nonPulseParameters['useTimerCB'] = self.cB_UseTimer.isChecked()
        self._nonPulseParameters['useIntervalTimerCB'] = self.cB_useIntervalMode.isChecked()
        self._nonPulseParameters['zeroAdjust'] = int(round(float(str(self.txEd_zeroAdjust.text()))))

    def showMessageBox(self, msg, winTitle='Error'):
        # shows a single string error message, or a list of strings as a series of messages
        mbx = QtGui.QMessageBox()
        mbx.setWindowTitle(winTitle)
        if type(msg) is str:
            message = msg
        elif type(msg) is list:
            message = ''
            for el in msg:
                message = message + el + '\n'
        mbx.setText(message)
        mbx.exec_()

    def enableTimerControls(self, isEnabled):
        # Enables or disables the timer controls and labels.
        # Set isEnabled to True to enable, False to disable
        self.cB_UseTimer.setEnabled(isEnabled)
        self.cB_useIntervalMode.setEnabled(isEnabled)
        if self.cB_UseTimer.isChecked():
            self.txEd_timerMin.setEnabled(isEnabled)
            self.lbl_Minutes.setEnabled(isEnabled)
        else:
            self.txEd_timerMin.setEnabled(False)
            self.lbl_Minutes.setEnabled(False)

        if self.cB_useIntervalMode.isChecked():
            self.lnEd_onTime.setEnabled(isEnabled)
            self.lnEd_offTime.setEnabled(isEnabled)
        else:
            self.lnEd_onTime.setEnabled(False)
            self.lnEd_offTime.setEnabled(False)

    def advanceTimer(self):
        if self.__timerUsed:
            self.__timerVal = self.__timerVal-1 # reduce by one second
            if self.__timerVal <= 0:
                timerString = self.makeTimerString(self.__timerVal)     # populate timer output before calling timer expired code
                self.lbl_CountDown.setText(timerString)
                self.timerExpired()
                self.__timer.stop()
        else:
            self.__timerVal = self.__timerVal+1 # increase by one second

        timerString = self.makeTimerString(self.__timerVal)
        self.lbl_CountDown.setText(timerString)

    def advanceIntervalTimer(self):
        if self._intervalTimerUsed:
            self._intervalTimerVal = self._intervalTimerVal-1 # reduce by one second
            if self._intervalTimerVal <= 0:
                self.intervalTimerExpired()

        timerString = self.makeTimerString(self._intervalTimerVal)
        self.lbl_intervalTime.setText(timerString)

    def makeTimerString(self, nsec):
        # creates a min:sec timer string out of number of seconds
        # INPUT
        # nsec is the number of seconds
        # OUTPUT
        # timerString is a string in hour:min:sec format

        nhour = int(math.floor(nsec/3600))
        nmin = int(math.floor((nsec-nhour*3600) / 60))
        nsec = int(math.fmod(nsec, 60))
        if nsec < 10:
            secString = '0'+str(nsec)
        else:
            secString = str(nsec)

        if nmin < 10:
            minString = '0'+str(nmin)
        else:
            minString = str(nmin)

        minSecString = minString + ':' + secString

        if nhour > 0:
            timerString = str(nhour) + ':' + minSecString
        else:
            timerString = minSecString

        return timerString

    def timerExpired(self):
        self.__timerExpired = True
        self.stopPulsing()

    def intervalTimerExpired(self):
        # Callback from expiration (not advancement) of the interval timer, which is used to time both the ON and OFF states. Toggles the state and starts the
        # pulsing if necessary.
        self._intervalTimerExpired = True
        self._intervalTimer.stop()
        # Based on which pulsing state we are in, toggle state
        if self._intervalTimerPulseState == ON:
            self._intervalTimerPulseState = OFF
            BBB.stopPulsing()
            self.startIntervalTimer(OFF)
            self.lbl_intervalState.setText('Not Pulsing')
            self.__mv_gif.stop()
        else:
            if self.__timerVal > 0 and self._globalPulsingState == ON:
                self._intervalTimerPulseState = ON
                BBB.startPulsing()
                self.startIntervalTimer(ON)
                self.lbl_intervalState.setText('Pulsing')
                self.__mv_gif.start()

    def EnableControls(self):
        self.pB_StartPulsing.setEnabled(True)
        self.pB_StopPulsing.setEnabled(False)
        self.pB_ResetTimer.setEnabled(True)
        self.enableTimerControls(True)
        self.txEd_EFieldAmpPos.setEnabled(True)
        self.txEd_EFieldAmpNeg.setEnabled(True)
        self.txEd_pulseDurationPos.setEnabled(True)
        self.txEd_pulseDurationNeg.setEnabled(True)
        self.txEd_pulseSpacing.setEnabled(True)
        self.txEd_dcBias.setEnabled(True)

    def DisableControls(self):
        self.pB_StopPulsing.setEnabled(True)
        self.pB_StartPulsing.setEnabled(False)
        self.pB_ResetTimer.setEnabled(False)
        self.enableTimerControls(False)
        self.txEd_EFieldAmpPos.setEnabled(False)
        self.txEd_EFieldAmpNeg.setEnabled(False)
        self.txEd_pulseDurationPos.setEnabled(False)
        self.txEd_pulseDurationNeg.setEnabled(False)
        self.txEd_pulseSpacing.setEnabled(False)
        self.txEd_dcBias.setEnabled(False)

    def _scrubNumericalInput(self, txtInputWidget, roundLevel):
        # Helper method for accepting numerical input from a text box. Takes input and rounds it, returning the rounded number and the associated string of the
        # rounded number
        # INPUTS
        # txtInputWidget is a text input widget that is meant to accept a single number as input, and has a text() method for reading and a setText() method for
        #   setting
        # roundLevel an integer giving the rounding level for the result, where 0 means nearest integer, 1 means to nearest 0.1, etc...
        # OUTPUTS
        # roundedVal is the number that is the rounded value
        # roundedString is the string version of the rounded value
        # validInput is True if the input is a valid number, False otherwise

        try:
            val = float(str(txtInputWidget.text()))
            roundedVal = round(val, roundLevel)
            if roundLevel == 0:
                roundedVal = int(roundedVal)
            roundedString = str(roundedVal)
            txtInputWidget.setText(roundedString)
            validInput = True
        except ValueError:
            txtInputWidget.clear()
            validInput = False
            roundedString = None
            roundedVal = None

        return roundedVal, roundedString, validInput

    def makeParametersDictObj(self):
        # pack current parameters into a single dictionary object. Note that these are not necessarily the parameters that are in the UI. The parameters must be
        # loaded from the UI first to pack those.
        dictObj = dict()
        dictObj['EFieldAmpPos'] = self.__pulseParams['EFieldAmpPos']
        dictObj['EFieldAmpNeg'] = self.__pulseParams['EFieldAmpNeg']
        dictObj['EFieldLobeDurationPos'] = self.__pulseParams['EFieldLobeDurationPos']
        dictObj['EFieldLobeDurationNeg'] = self.__pulseParams['EFieldLobeDurationNeg']
        dictObj['PulseSpacing'] = self.__pulseParams['PulseSpacing']
        dictObj['dcBias'] = self.__pulseParams['dcBias']

        dictObj['IntervalOnTime'] = self._nonPulseParameters['IntervalOnTime']
        dictObj['IntervalOffTime'] = self._nonPulseParameters['IntervalOffTime']
        dictObj['MainTimer'] = self._nonPulseParameters['MainTimer']
        dictObj['useTimerCB'] = self._nonPulseParameters['useTimerCB']
        dictObj['useIntervalTimerCB'] = self._nonPulseParameters['useIntervalTimerCB']
        dictObj['zeroAdjust'] = self._nonPulseParameters['zeroAdjust']

        return dictObj

    def unpackParametersDictObj(self, dictObj):
        # Loads class parameters from dictionary object
        # Unpack parameters
        self.__pulseParams['EFieldAmpPos'] = dictObj['EFieldAmpPos']
        self.__pulseParams['EFieldAmpNeg'] = dictObj['EFieldAmpNeg']
        self.__pulseParams['EFieldLobeDurationPos'] = dictObj['EFieldLobeDurationPos']
        self.__pulseParams['EFieldLobeDurationNeg'] = dictObj['EFieldLobeDurationNeg']
        self.__pulseParams['PulseSpacing'] = dictObj['PulseSpacing']
        self.__pulseParams['dcBias'] = dictObj['dcBias']

        self.txEd_EFieldAmpPos.setText(str(dictObj['EFieldAmpPos']))
        self.txEd_EFieldAmpNeg.setText(str(dictObj['EFieldAmpNeg']))
        self.txEd_pulseDurationPos.setText(str(dictObj['EFieldLobeDurationPos']))
        self.txEd_pulseDurationNeg.setText(str(dictObj['EFieldLobeDurationNeg']))
        self.txEd_pulseSpacing.setText(str(dictObj['PulseSpacing']))
        self.txEd_dcBias.setText(str(dictObj['dcBias']))

        # non-pulse parameters
        self._nonPulseParameters['IntervalOnTime'] = dictObj['IntervalOnTime']
        self._nonPulseParameters['IntervalOffTime'] = dictObj['IntervalOffTime']
        self._nonPulseParameters['MainTimer'] = dictObj['MainTimer']
        self._nonPulseParameters['useTimerCB'] = dictObj['useTimerCB']
        self._nonPulseParameters['useIntervalTimerCB'] = dictObj['useIntervalTimerCB']
        self._nonPulseParameters['zeroAdjust'] = dictObj['zeroAdjust']

        self.txEd_timerMin.setText(str(dictObj['MainTimer']))
        self.lnEd_onTime.setText(str(dictObj['IntervalOnTime']))
        self.lnEd_offTime.setText(str(dictObj['IntervalOffTime']))
        self.cB_useIntervalMode.setChecked(dictObj['useIntervalTimerCB'])
        self.cB_UseTimer.setChecked(dictObj['useTimerCB'])
        self.txEd_zeroAdjust.setText(str(dictObj['zeroAdjust']))
        self.zeroAdjustTextEdited()  # zero adjust must be sent immediately, as it is not sent with each start pulse command

    def showMessage(self):
        self.showMessageBox('Got Here!')


# Advanced Config Dialog
class AdvancedConfigDlg(Ui_AdvancedConfigBaseClass, Ui_AdvancedConfigDlg):
    def __init__(self, parent=None):
        Ui_AdvancedConfigBaseClass.__init__(self, parent)
        self.setupUi(self)

        self.pB_OK.clicked.connect(self.close)

    @property
    def disableWarnings(self):
        return self.cB_disableFaultWarnings.isChecked()


# Functions
def validateParameter(parameter, minVal, maxVal, includeLowerBound=True, includeUpperBound=True):
    # Checks whether a parameter is within a given interval
    if includeLowerBound:
        valid = parameter >= minVal
    else:
        valid = parameter > minVal
    if includeUpperBound:
        valid = valid and parameter <= maxVal
    else:
        valid = valid and parameter < maxVal

    return valid


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

