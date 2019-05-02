import pickle
import numpy as np
import matplotlib.pyplot as plt
import SpectrumGraphData

"""Helper meathods for Server Class"""

#reads from spectrum file to create SpectrumGraphData
def readSpec(file):
    trace = np.load(file)
    width = pickle.load(file)
    frequency = pickle.load(file)
    span = pickle.load(file)
    ref_level = pickle.load(file)
    return SpectrumGraphData(trace, width, frequency, span, ref_level)

#Graphs spectrum data, creates window if it does not exist
def specGraph(minRef, maxRef, startF, endF, freqStepSize, ydata):
    xdata = np.arange(startF, endF+freqStepSize, freqStepSize)
    for i in range(len(ydata)):
        ydata[i] = ydata[i]+maxRef/2.0
    if plt.fignum_exists(1):
        plt.clf()
        lines = plt.plot(xdata, ydata)
        plt.setp(lines, color='g')
        plt.axis([startF, endF, minRef, maxRef])
        plt.xticks(np.arange(startF, endF + 1, (endF - startF) / 4))
        plt.yticks(np.arange(minRef, maxRef + 1, (maxRef - minRef) / 4))
        plt.ylabel('Power Level')
        plt.xlabel('Frequency (Hz)')
        plt.title('Spectrum')
        plt.show(block=False)
        plt.pause(.01)
    # Creates a plot if none exists
    else:
        plt.figure(num=1,figsize=(13, 5))
        lines = plt.plot(xdata, ydata)
        plt.setp(lines, color='g')
        plt.axis([startF, endF, minRef, maxRef])
        plt.xticks(np.arange(startF, endF + 1, (endF - startF) / 4))
        plt.yticks(np.arange(minRef, maxRef + 1, (maxRef - minRef) / 4))
        plt.ylabel('Power Level')
        plt.xlabel('Frequency (Hz)')
        plt.title('Spectrum')
        plt.show(block=False)
        plt.pause(.01)

#translates command to be sent to server and client
def parseCommand(CommandIn):
    command = CommandIn.lower()
    command = command.split()
    commandOut = None
    referenceLevel = '0.0'
    frequency = '1e9'
    span = '40e6'
    time = '1.0'
    width = '801'
    minRef = '-100.0'
    IFPower = '-30.0'
    TriggerTime = '00:00:00'
    TriggerTimeDuration = '10.0'
    connectionNumber = '0'

    try:
        if command[0] == 'man':
            commandOut = '\n\n\nInstructions\n\n\n' \
                  'connect: Connects to an RSAController\n' \
                  'setup: Enters setup mode for the RSAController. User can change the center frequency, reference level, triggers, and data to acquire.\n' \
                  'data: Sets the RSA to record iq, spectrum or dpx data\n' \
                  '      Flags\n' \
                  '          Data Type Flags (Required): Must be set first!\n' \
                  '              -d: DPX data\n' \
                  '                  Parameters (Optional)\n' \
                  '                      -b: Span of data acquired around the center frequency. Default: 40e6\n' \
                  '                      -w: Number of points between start and end frequency. Default and Max: 801\n' \
                  '                      -m: Minimum power level of recorded data. Default: -100.0\n' \
                  '                      -t: Time length of DPX frame. Default: 1.0 (s)\n' \
                  '                  Examples\n' \
                  '                      data -d -b 100e6 -t 2.0\n' \
                  '                      data -d -b 100e6 -w 800 -t 1.5 -m -75.0\n' \
                  '                      data -d -m -90.0 -t 2.0 \n' \
                  '              -s: Spectrum data\n' \
                  '                  Parameters (Optional)\n' \
                  '                      -b: Span of data acquired around the center frequency. Default: 40e6\n' \
                  '                      -w: Number of points between start and end frequency. Default and Max: 801\n' \
                  '                  Examples\n' \
                  '                  data -s -b 100e6 -w 800\n' \
                  '                  data -s -w 200\n' \
                  '                  data -s -w 800 -b 1e9 \n' \
                  '              -i: IQ data\n' \
                  '                  Parameters (Optional)\n' \
                  '                      -b: Span of data acquired around the center frequency. Default: 40e6\n' \
                  '                      -t: Time length of IQ data frame. Default and Max: 1.0 (s)\n' \
                  '                  Examples\n' \
                  '                  data -i -b 100e6\n' \
                  '                  data -i -t 2.0\n' \
                  '                  data -i -t 1.5 -b 1e9 \n' \
                  'frequency: Sets the center frequency of the RSA. Default: 1e9\n' \
                  '  Flags\n' \
                  '      -f: Frequency (Hz)\n' \
                  '  Examples\n' \
                  '      frequency #Sets the frequency to 1e9 Hz\n' \
                  '      frequency -f 100e6\n' \
                  'refLevel: Change the reference level of the RSA\n' \
                  '  Flags\n' \
                  '      -r: Reference level. Default -100\n' \
                  '  Examples\n' \
                  '      refLevel #Sets the reference level to -100\n' \
                  '      refLevel -r -10\n' \
                  'trigger: Set the RSA to trigger.\n' \
                  'triggeroff: Turns off the trigger.\n' \
                  'exit: Exits the setup mode and gets the RSA ready to capture data\n' \
                  'start: The RSAController will start recording data and send it to the server. If there is a trigger, data will only be recorded if the trigger is met\n' \
                  'stop: Stops the RSAController from recording data\n'

            return False, commandOut
        elif command[0] == 'setup':
            commandOut = command[0]
            return True, commandOut

        elif command[0] == 'change':
            commandOut = command[0]
            del command[0]
            if len(command) > 2:
                commandOut = 'Too Many Parameters'
                return False, commandOut
            while len(command) > 0:
                if command[0] == '-c':
                    del command[0]
                    if not command:
                        commandOut = 'Missing connection number'
                        return False, commandOut
                    connectionNumber = command[0]
                    del command[0]
                else:
                    commandOut = 'Invalid Flag'
                    return False, commandOut
            commandOut = commandOut + ' ' + frequency
            return True, commandOut

        elif command[0] == 'start':
            commandOut = command[0]
            return True, commandOut

        elif command[0] == 'stop':
            commandOut = command[0]
            return True, commandOut

        elif command[0] == 'frequency':
            commandOut = command[0]
            del command[0]
            if len(command) > 2:
                commandOut = 'Too Many Parameters'
                return False, commandOut
            while len(command) > 0:
                if command[0] == '-f':
                    del command[0]
                    if not command:
                        commandOut = 'Missing Center Frequency'
                        return False, commandOut
                    frequency = command[0]
                    del command[0]
                else:
                    commandOut = 'Invalid Flag'
                    return False, commandOut
            commandOut = commandOut + ' ' + frequency
            return True, commandOut

        elif command[0] == 'reflevel':
            del command[0]
            if len(command) > 2:
                commandOut = 'Too Many Parameters'
                return False, commandOut
            commandOut = 'refLevel'
            while len(command) > 0:
                if command[0] == '-r':
                    del command[0]
                    if not command:
                        commandOut = 'Missing Reference Level'
                        return False, commandOut
                    referenceLevel = command[0]
                    del command[0]
                else:
                    commandOut = 'Invalid Flag'
                    return False, commandOut
            commandOut = commandOut + ' ' + referenceLevel
            return True, commandOut

        elif command[0] == 'exit':
            commandOut = command[0]
            return True, commandOut

        elif command[0] == 'connect':
            commandOut = command[0]
            return True, commandOut

        elif command[0] == 'data':
            if len(command) == 1:
                commandOut = 'Missing Data Type'
                return False, commandOut
            commandOut = command[0]
            del command[0]
            if command[0] == '-d':
                del command[0]
                if len(command) > 8:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                commandOut = commandOut + ' dpx'
                while len(command) >= 1:
                    if command[0] == '-b':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Bandwidth'
                            return False, commandOut
                        span = command[0]
                        del command[0]
                    elif command[0] == '-m':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Minimum Power Level'
                            return False, commandOut
                        minRef = command[0]
                        del command[0]
                    elif command[0] == '-w':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Number Of Steps'
                            return False, commandOut
                        width = command[0]
                        del command[0]
                    elif command[0] == '-t':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Time Of Acquisition'
                            return False, commandOut
                        time = command[0]
                        del command[0]
                    else:
                        commandOut = 'Invalid Flag'
                        return False, commandOut
                commandOut = commandOut + " " + span + " " + minRef + " " + width + " " + time
                return True, commandOut

            elif command[0] == '-s':
                del command[0]
                if len(command) > 4:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                commandOut = commandOut + ' spec'
                while len(command) > 0:
                    if command[0] == '-b':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Bandwidth'
                            return False, commandOut
                        span = command[0]
                        del command[0]
                    elif command[0] == '-w':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Steps'
                            return False, commandOut
                        width = command[0]
                        del command[0]
                    else:
                        commandOut = 'Invalid Flag'
                        return False, commandOut
                commandOut = commandOut + " " + span + " " + width
                return True, commandOut

            elif command[0] == '-i':
                del command[0]
                if len(command) > 4:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                commandOut = commandOut + ' iq'
                while len(command) >= 1:
                    if command[0] == '-b':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Bandwidth'
                            return False, commandOut
                        span = command[0]
                        del command[0]
                    elif command[0] == '-t':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Time Of Acquisition'
                            return False, commandOut
                        time = command[0]
                        del command[0]
                    else:
                        commandOut = 'Invalid Flag'
                        return False, commandOut
                commandOut = commandOut + ' ' + span + ' ' + time
                return True, commandOut
            else:
                commandOut = 'Incorrect Data Type'
                return False, commandOut

        elif command[0] == 'trigger':
            if len(command) == 1:
                commandOut = 'Missing Trigger Source'
                return False, commandOut
            commandOut = command[0]
            del command[0]
            if command[0] == '-p':
                commandOut = commandOut + ' p'
                del command[0]
                if len(command) > 2:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                while len(command) > 0:
                    if command[0] == '-l':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Power Trigger Level'
                            return False, commandOut
                        IFPower = command[0]
                        del command[0]
                    else:
                        commandOut = 'Invalid Flag'
                        return False, commandOut
                commandOut = commandOut + ' ' + IFPower
                return True, commandOut
            elif command[0] == '-a':
                commandOut = commandOut + ' t'
                del command[0]
                if len(command) > 4:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                while len(command) > 0:
                    if command[0] == '-y':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Time Trigger Duration'
                            return False, commandOut
                        TriggerTimeDuration = command[0]
                        del command[0]
                    elif command[0] == '-x':
                        del command[0]
                        if not command:
                            commandOut = 'Missing Time Of Trigger'
                            return False, commandOut
                        TriggerTime = command[0]
                        del command[0]
                    else:
                        commandOut = 'Invalid Flag'
                        return False, commandOut
                commandOut = commandOut + ' ' + TriggerTime + ' ' + TriggerTimeDuration
                return True, commandOut
            elif command[0] == '-e':
                if len(command) > 1:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                commandOut = commandOut + ' ext'
                return True, commandOut
            elif command[0] == '-f':
                if len(command) > 1:
                    commandOut = 'Too Many Parameters'
                    return False, commandOut
                commandOut = commandOut + ' f'
                return True, commandOut
            else:
                commandOut = 'Incorrect Trigger Source'
                return False, commandOut
        else:
            return False, commandOut
    except:
        commandOut = 'Error'
        return False, commandOut