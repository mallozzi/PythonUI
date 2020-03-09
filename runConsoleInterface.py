import ConsoleManager as CM

cm = CM.ConsoleManager()

cm.loadSavedParameters()

done = False
while done == False:
    commandString = raw_input('Enter Console Command: ')
    commandStringList = commandString.split()  # splits on white space
    if len(commandStringList) > 0: # Handle the case where input is empty
        cmd = commandStringList[0]
    else:
        cmd = ''
    
    if cmd == 'exit':
        cm.stopPulsing()
        done = True
    elif cmd == 'set':
        paramKey = commandStringList[1]
        paramValue = commandStringList[2]
        cm.setParameter(paramKey, paramValue)
        cm.stopPulsing()
    elif cmd == 'params':
        cm.printParameters()
    elif cmd == 'save':
        cm.saveParameters()
        print('Parameters Saved: ')
        cm.printParameters()
    elif cmd == 'load':
        cm.loadSavedParameters()
    elif cmd == 'start':
        cm.startPulsing()
    elif cmd == 'stop':
        cm.stopPulsing()
    elif cmd == 'help':
        print('\nValid parameter names: EFieldAmpPos, PulseSpacing, EFieldLobeDurationPos, preBias')
        print("example: type 'set EFieldAmpPos 1.09' to set the field amplitude to 1.09")
        print("To start pulsing, type 'start', to stop pulsing type 'stop'")
        print("To view current parameters, type 'params'")
        print('')
    else:
        print('Invalid Command')
        
        
print('Exiting Console Interface. Current Parameters: ')
cm.printParameters()
    