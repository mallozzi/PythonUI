import BeagleboneControl as BBC
import Hardware_Constants as HWC
import csv
import os.path
import math
import time

class ConsoleManager:
# This class is only used when communicating with the microcontroller in console mode, rather than through the UI. It manages the
# data.

    def __init__(self):
        # pulse properties
        self.__pulseParams = {'EFieldAmpPos': 0.05, 'PulseSpacing': 20, 'EFieldLobeDurationPos': 10, 'preBias': 0}
        
    def saveParameters(self):
        f = open('StoredParameters.txt', 'w+')
        dw = csv.DictWriter(f, self.__pulseParams.keys())
        dw.writeheader()
        dw.writerow(self.__pulseParams)
        f.close()
        print('Parameters have been saved')

    def loadSavedParameters(self):
        if os.path.isfile('StoredParameters.txt'):
            f = open('StoredParameters.txt', 'r')
            dr = csv.DictReader(f)
            for row in dr:
                dictObj = row
            self.__pulseParams = dictObj
            # need to convert from strings to numbers
            for ky in self.__pulseParams:
                self.setParameter(ky, self.__pulseParams[ky])
                
            print ('\nParameters loaded from file:')
            self.printParameters()
        else:
            pass
            
    def setParameter(self, paramKey, value):
        if paramKey not in self.__pulseParams:
            print('Error: invalid parameter key')
        else:
            # convert to appropriate type
            if paramKey == 'EFieldAmpPos':
                numVal = float(value)
            elif paramKey == 'PulseSpacing':
                numVal = int(value)
            elif paramKey == 'EFieldLobeDurationPos':
                numVal = int(value)
            elif paramKey == 'preBias':
                numVal = int(value)
                
            self.__pulseParams[paramKey] = numVal
            self.printParameters()
        
    def printParameters(self):       
        print('\nElectric Field Amplitude: ' + str(self.__pulseParams['EFieldAmpPos']) + ' V/m')
        print('Pulse lobe duration: ' + str(self.__pulseParams['EFieldLobeDurationPos']) + ' ms')
        print('Spacing between pulses (end to beginning) ' + str(self.__pulseParams['PulseSpacing']) + ' ms')
        print('Pre-bias value: ' + str(self.__pulseParams['preBias']) )
        print('')
        
    def startPulsing(self):
        transmissionVerified = self.sendPulseParametersToMCU()
        time.sleep(0.01)
        if transmissionVerified:
            BBC.startPulsing()
        
    def stopPulsing(self):
        BBC.stopPulsing()
        
    def sendPulseParametersToMCU(self):
    # Sends pulse parameters to the MCU and reads them back to make sure they are accurate
    # returns True if transmission was verified, False if verification failed.
        transmissionVerified = BBC.sendPulseParametersToMCU(self.__pulseParams)
        if transmissionVerified == False:
            print("\n\n\n\n\n ERROR IN PARAMETER TRANSMISSION \n\n\n\n")
        return transmissionVerified
        
    

