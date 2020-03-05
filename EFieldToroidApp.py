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

# --------------------------------

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

#registerMap = {'EFieldAmp': 1, 'EFieldDuration': 2}
# Global Constants
ON = 1
OFF = 0

class MyApp(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # Properties
        self.__pulseParams = {'EFieldAmp': 0.05, 'PulseSpacing': 20, 'EFieldLobeDuration': 10, 'preBias': 26}
        self._nonPulseParameters = {'IntervalOnTime': .3, 'IntervalOffTime': .2, 'MainTimer': 14, 'useTimerCB': True, 'useIntervalTimerCB': False}
        self._globalPulsingState = OFF  # either ON or OFF, depending on whether we are in pulsing mode. Note that we may be in an 'off' pulsing interval state,
                                        # but be in an ON global pulsing state

        # initialization
        pxmp = QtGui.QPixmap('OLogo.jpg')
        self.lbl_Logo.setPixmap(pxmp)

        self.__mv_gif = QtGui.QMovie('7SUb.gif')
        self.__mv_gif.setCacheMode(QtGui.QMovie.CacheAll)
        self.lbl_gif.setMovie(self.__mv_gif)
        self.__mv_gif.start()
        self.__mv_gif.stop()
        self.__mv_gif.jumpToFrame(1)

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

        # Timer for current monitoring
        self.__currentTimer = QtCore.QTimer()
        self.__currentTimer.timeout.connect(self.checkCurrent)

        # SIGNALS for callback functions
        self.txEd_EFieldAmp.editingFinished.connect(self.EFieldAmpTextEdited)
        self.txEd_pulseDuration.editingFinished.connect(self.pulseDurationTextEdited)
        self.txEd_pulseSpacing.editingFinished.connect(self.pulseSpacingTextEdited)
        self.txEd_timerMin.editingFinished.connect(self.timerValTextEdited)
        self.pB_StartPulsing.clicked.connect(self.startPulsing)
        self.pB_StopPulsing.clicked.connect(self.stopPulsing)
        self.pB_Verify.clicked.connect(self.verifyPulseParams)
        self.pB_ResetTimer.clicked.connect(self.resetTimer)
        self.act_Store_Parameters.triggered.connect(self.storeParameters)
        self.act_Load_Parameters.triggered.connect(self.loadStoredParameters)
        self.cB_UseTimer.stateChanged.connect(self.timerStateChanged)
        self.cB_useIntervalMode.stateChanged.connect(self.intervalStateChanged)
        self.cB_AdvancedControls.stateChanged.connect(self.advancedStateChanged)
        self.pB_resetMCU.clicked.connect(self.resetMCU)
        self.pB_readCurrent.clicked.connect(self.readCurrent)
        self.lnEd_onTime.editingFinished.connect(self.intervalTimerOnMinTextEdited)
        self.lnEd_offTime.editingFinished.connect(self.intervalTimerOffMinTextEdited)

        # Load parameters from file
        self.loadStoredParameters()

        # Disable advanced controls
        self.DisableAdvancedControls()

# *************  CALLBACKS  *************************

    def EFieldAmpTextEdited(self):
        try:
            val = float(str(self.txEd_EFieldAmp.text()))
            roundedVal = round(val, 2)
            newText = str(roundedVal)
            self.txEd_EFieldAmp.setText(newText)
        except ValueError:
            self.txEd_EFieldAmp.clear()

    def pulseDurationTextEdited(self):
        try:
            val = float(str(self.txEd_pulseDuration.text()))
            roundedVal = int(round(val, 0))
            newText = str(roundedVal)
            self.txEd_pulseDuration.setText(newText)
        except ValueError:
            self.txEd_pulseDuration.clear()

    def pulseSpacingTextEdited(self):
        try:
            val = float(str(self.txEd_pulseSpacing.text()))
            roundedVal = int(round(val, 0))
            newText = str(roundedVal)
            self.txEd_pulseSpacing.setText(newText)
        except ValueError:
            self.txEd_pulseSpacing.clear()

    def timerValTextEdited(self):
        try:
            val = float(str(self.txEd_timerMin.text()))
            roundedVal = int(round(val, 0))
            newText = str(roundedVal)
            self.txEd_timerMin.setText(newText)
        except ValueError:
            self.txEd_timerMin.clear()

    def intervalTimerOnMinTextEdited(self):
        try:
            val = float(str(self.lnEd_onTime.text()))
            roundedVal = round(val, 1)
            newText = str(roundedVal)
            self.lnEd_onTime.setText(newText)
        except ValueError:
            self.lnEd_onTime.clear()

    def intervalTimerOffMinTextEdited(self):
        try:
            val = float(str(self.lnEd_offTime.text()))
            roundedVal = round(val, 1)
            newText = str(roundedVal)
            self.lnEd_offTime.setText(newText)
        except ValueError:
            self.lnEd_offTime.clear()

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
            BBB.sendPulseParametersToMCU(self.__pulseParams)
            BBB.startPulsing()
            self.DisableControls()
            self.__mv_gif.start()

            # start current monitoring timer
            sampleInterval_ms = 201.313  # interval to check current in ms. Choose to be something less likely to be synchronous with pulsing.
      #      self.__currentTimer.start(sampleInterval_ms)

    def startIntervalTimer(self, whichState):
        if self._globalPulsingState == ON:
            self._intervalTimerPulseState = whichState
            self._intervalTimerInitVal = self.getIntervalTimerInitVal(whichState)
            self._intervalTimerVal = self._intervalTimerInitVal * 60  # seconds
            self._intervalTimerExpired = False
            self._intervalTimer.start(1000)  # update every second
            self.lbl_intervalTime.setText(self.makeTimerString(self._intervalTimerVal))

    def stopIntervalTimer(self):
        self._intervalTimer.stop()
        self._intervalTimerPulseState = OFF
        self.lbl_intervalTime.setText(self.makeTimerString(0))

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
        BBB.stopPulsing()
    #    self.__currentTimer.stop()  # current monitoring
        self.__timer.stop()
        self.__mv_gif.stop()
        self.__mv_gif.jumpToFrame(1)
        self.pB_Verify.setFocus()
        self.EnableControls()
        self._globalPulsingState = OFF
        self.stopIntervalTimer()
        if self.__timerUsed and self.__timerExpired:
            self.showMessageBox('Pulsing Terminated After '+str(self.__timerInitVal)+ ' minutes','Info')

    def verifyPulseParams(self):
        self.loadPulseParamsFromUI()
        # set pre-bias if auto-prebias is checked
        if self.cB_AutoPreBias.isChecked():
            EField = self.__pulseParams['EFieldAmp']
            preBiasInt = MCFuncs.calcPreBiasInt(EField)
            self.txEd_preBias.setText(str(preBiasInt))

        self.loadPulseParamsFromUI()
        isValid, msg = MCFuncs.validatePulseParameters(self.__pulseParams)
        if not isValid:
            self.showMessageBox(msg, 'Invalid Parameter')

        return isValid, msg

    def storeParameters(self):
        self.loadPulseParamsFromUI()
        # pack parameters into a single dictionary object
        dictObj = dict()
        dictObj['EFieldAmp'] = self.__pulseParams['EFieldAmp']
        dictObj['EFieldLobeDuration'] = self.__pulseParams['EFieldLobeDuration']
        dictObj['PulseSpacing'] = self.__pulseParams['PulseSpacing']
        dictObj['preBias'] = self.__pulseParams['preBias']

        dictObj['IntervalOnTime'] = self._nonPulseParameters['IntervalOnTime']
        dictObj['IntervalOffTime'] = self._nonPulseParameters['IntervalOffTime']
        dictObj['MainTimer'] = self._nonPulseParameters['MainTimer']
        dictObj['useTimerCB'] = self._nonPulseParameters['useTimerCB']
        dictObj['useIntervalTimerCB'] = self._nonPulseParameters['useIntervalTimerCB']

        with open('StoredParameters.txt', 'w+') as fp:
            json.dump(dictObj, fp, indent=4)
        self.showMessageBox('Parameters have been stored', 'Info')

    def loadStoredParameters(self):
        if os.path.isfile('StoredParameters.txt'):
            with open('StoredParameters.txt', 'r') as fp:
                dictObj = json.load(fp)

                # Unpack parameters
                self.__pulseParams['EFieldAmp'] = dictObj['EFieldAmp']
                self.__pulseParams['EFieldLobeDuration'] = dictObj['EFieldLobeDuration']
                self.__pulseParams['PulseSpacing'] = dictObj['PulseSpacing']
                self.__pulseParams['preBias'] = dictObj['preBias']

                self.txEd_EFieldAmp.setText(str(dictObj['EFieldAmp']))
                self.txEd_pulseDuration.setText(str(dictObj['EFieldLobeDuration']))
                self.txEd_pulseSpacing.setText(str(dictObj['PulseSpacing']))
                self.txEd_preBias.setText(str(dictObj['preBias']))

                # non-pulse parameters
                self._nonPulseParameters['IntervalOnTime'] = dictObj['IntervalOnTime']
                self._nonPulseParameters['IntervalOffTime'] = dictObj['IntervalOffTime']
                self._nonPulseParameters['MainTimer'] = dictObj['MainTimer']
                self._nonPulseParameters['useTimerCB'] = dictObj['useTimerCB']
                self._nonPulseParameters['useIntervalTimerCB'] = dictObj['useIntervalTimerCB']

                self.txEd_timerMin.setText(str(dictObj['MainTimer']))
                self.lnEd_onTime.setText(str(dictObj['IntervalOnTime']))
                self.lnEd_offTime.setText(str(dictObj['IntervalOffTime']))
                self.cB_useIntervalMode.setChecked(dictObj['useIntervalTimerCB'])
                self.cB_UseTimer.setChecked(dictObj['useTimerCB'])

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

    def resetMCU(self):
        self.stopPulsing()
        BBB.resetMCU()
        self.showMessageBox('Microcontroller reset command sent', 'Info')

    def readCurrent(self):
        # Reads current from ADC in each channel are shows value in a message box.
        duration_ms = 200
        current1, current2 = BBB.readCurrent(duration_ms)
        msg = 'Channel 1:   ' + str(round(current1,2)) + ' Amps \n' + 'Channel 2:   ' + str(round(current2,2)) + ' Amps'
        self.showMessageBox(msg, 'Current Output')

    def checkCurrent(self):
        # Performs a quick check on the current for safety. Compares current to the limit set up in Hardware_Constants
        # and reports whether the current level passed or not. The check is short enough that it may not pick up the
        # maximum current in a pulse, but is meant to catch consistently high values.
        # OUTPUT
        # testPassed is True if the current was less than or equal to the limit, False if it was greater than the limit.

        duration_ms = 50
        current1, current2 = BBB.readCurrent(duration_ms)
        upperLimit = HW.CURRENT_LIMIT
        testPassed = current1 <= upperLimit and current2 <= upperLimit
        if not testPassed:
            self.stopPulsing()
            msg = 'Current limit of ' + str(upperLimit) + ' Amps exceeded. Current was ' + str(round(max(current1,current2),2)) + ' Amps.'
            self.showMessageBox(msg)

    def advancedStateChanged(self):
        if self.cB_AdvancedControls.isChecked():
            self.EnableAdvancedControls()
        else:
            self.DisableAdvancedControls()

    def resetTimer(self):
        self.lbl_CountDown.setText(self.makeTimerString(self.__timerInitVal*60))

# *************  NON-CALLBACK METHODS ***************

    def loadPulseParamsFromUI(self):
        self.__pulseParams['EFieldAmp'] = float(str(self.txEd_EFieldAmp.text()))
        self.__pulseParams['EFieldLobeDuration'] = int(round(float(str(self.txEd_pulseDuration.text()))))
        self.__pulseParams['PulseSpacing'] = int(round(float(str(self.txEd_pulseSpacing.text()))))
        self.__pulseParams['preBias'] = int(round(float(str(self.txEd_preBias.text()))))

        self._nonPulseParameters['IntervalOnTime'] = float(str(self.lnEd_onTime.text()))
        self._nonPulseParameters['IntervalOffTime'] = float(str(self.lnEd_offTime.text()))
        self._nonPulseParameters['MainTimer'] = int(str(self.txEd_timerMin.text()))
        self._nonPulseParameters['useTimerCB'] = self.cB_UseTimer.isChecked()
        self._nonPulseParameters['useIntervalTimerCB'] = self.cB_useIntervalMode.isChecked()

    def showMessageBox(self, msg, winTitle='Error'):
        mbx = QtGui.QMessageBox()
        mbx.setWindowTitle(winTitle)
        mbx.setText(msg)
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
            BBB.setGlobalEnable(HW.DISABLE)
            BBB.stopPulsing()
            self.startIntervalTimer(OFF)
            self.__mv_gif.stop()
        else:
            if self.__timerVal > 0 and self._globalPulsingState == ON:
                self._intervalTimerPulseState = ON
                BBB.setGlobalEnable(HW.ENABLE)
                BBB.startPulsing()
                self.startIntervalTimer(ON)
                self.__mv_gif.start()

    def EnableControls(self):
        self.pB_StartPulsing.setEnabled(True)
        self.pB_StopPulsing.setEnabled(False)
        self.pB_ResetTimer.setEnabled(True)
        self.enableTimerControls(True)
        self.txEd_EFieldAmp.setEnabled(True)
        self.txEd_pulseDuration.setEnabled(True)
        self.txEd_pulseSpacing.setEnabled(True)
        self.cB_AdvancedControls.setEnabled(True)

    def DisableControls(self):
        self.pB_StopPulsing.setEnabled(True)
        self.pB_StartPulsing.setEnabled(False)
        self.pB_ResetTimer.setEnabled(False)
        self.enableTimerControls(False)
        self.txEd_EFieldAmp.setEnabled(False)
        self.txEd_pulseDuration.setEnabled(False)
        self.txEd_pulseSpacing.setEnabled(False)
        self.cB_AdvancedControls.setEnabled(False)

    def EnableAdvancedControls(self):
        self.txEd_preBias.setEnabled(True)
        self.pB_readCurrent.setEnabled(True)
        self.cB_AutoPreBias.setEnabled(True)

    def DisableAdvancedControls(self):
        self.txEd_preBias.setEnabled(False)
        self.pB_readCurrent.setEnabled(False)
        self.cB_AutoPreBias.setEnabled(False)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

