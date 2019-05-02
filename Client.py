import os
from time import sleep
import numpy as np
from RSA_API import *
import socket
from threading import Thread, Condition
import datetime
import SpectrumGraphData
import DPXGraphData
import IQGraphData
import ClientHelper as CH

#file extensions for data types
DPX_DATA_FILE_EXTENSION = ".dsi"
SPEC_DATA_FILE_EXTENSION = ".ssi"
IQ_DATA_FILE_EXTENSION = ".isi"
#root path for temporary storage, needs to change on different devices
DATA_PATH = "C:/Users/thema/OneDrive/Documents/Malcolm's_Things/Fall 2018/temp"

#IP of server, needs to change when moveing network
SERVER_IP = "10.17.186.55"

#Sets directory to RSA API
os.chdir("C:\Tektronix\RSA_API\lib\\x64")
r = os.getcwd()
#Makes sure directory is correct
print("Current directory is %s" % r)


class Client(object):
    """A client will listen to commands comming from the server and pass them onto the RSA, it will also send data back
    to the server when necessary"""

    def __init__(self):
        self.rsa = cdll.LoadLibrary("RSA_API.dll")
        self.s = socket.socket()
        port = 12345
        while(True):
            try:
                self.s.connect((SERVER_IP, port))
            except:
                print("No Server!")
                sleep(1)
            else:
                break
        self.refLevel = 0.0
        self.minLevel = -100.0
        self.centerFreq = 1.5e9
        self.dataSpan = 40.0e6
        self.dataMode = "n"
        self.triggered = False
        self.dataThread = None
        self.threadActive = False
        self.timeSpan = 0
        self.time = None
        self.search_connect()
        self.setup = False
        self.triggerCommand = ''
        self.dataCommand = ''
        self.chunk_ready = False
        self.crcond = Condition()
        self.file_ready = False
        self.frcond = Condition()

    #connect to RSA
    def search_connect(self):
        numFound = c_int(0)
        intArray = c_int * DEVSRCH_MAX_NUM_DEVICES
        deviceIDs = intArray()
        deviceSerial = create_string_buffer(DEVSRCH_SERIAL_MAX_STRLEN)
        deviceType = create_string_buffer(DEVSRCH_TYPE_MAX_STRLEN)
        apiVersion = create_string_buffer(DEVINFO_MAX_STRLEN)

        CH.err_check(self.rsa.DEVICE_GetAPIVersion(apiVersion))
        print('API Version {}'.format(apiVersion.value.decode()))

        CH.err_check(self.rsa.DEVICE_Search(byref(numFound), deviceIDs,
                                    deviceSerial, deviceType))

        if numFound.value < 1:
            # rsa.DEVICE_Reset(c_int(0))
            print('No instruments found. Exiting script.')
            exit()
        elif numFound.value == 1:
            print('One device found.')
            print('Device type: {}'.format(deviceType.value.decode()))
            print('Device serial number: {}'.format(deviceSerial.value.decode()))
            CH.err_check(self.rsa.DEVICE_Connect(deviceIDs[0]))
        else:
            # corner case
            print('2 or more instruments found. Enumerating instruments, please wait.')
            for inst in deviceIDs:
                CH.err_check(self.rsa.DEVICE_Connect(inst))
                CH.err_check(self.rsa.DEVICE_GetSerialNumber(deviceSerial))
                CH.err_check(self.rsa.DEVICE_GetNomenclature(deviceType))
                print('Device {}'.format(inst))
                print('Device Type: {}'.format(deviceType.value))
                print('Device serial number: {}'.format(deviceSerial.value))
                CH.err_check(self.rsa.DEVICE_Disconnect())
            # note: the API can only currently access one at a time
            selection = 1024
            while (selection > numFound.value - 1) or (selection < 0):
                selection = int(input('Select device between 0 and {}\n> '.format(numFound.value - 1)))
            CH.err_check(self.rsa.DEVICE_Connect(deviceIDs[selection]))
            CH.err_check(self.rsa.CONFIG_Preset())

    #handle a command (or string of commands) comming from the server
    def handleCommand(self, command):
        main_command = command.split('|')[0]
        if(main_command == 'c_r'):
            with self.crcond:
                self.chunk_ready = True
                self.crcond.notify()
        elif(main_command == 'f_r'):
            with self.frcond:
                self.file_ready = True
                self.frcond.notify()
        elif(main_command == 'stop'):
            self.stop()
            if(self.setup == True):
                self.setup = False
                self.setSettings()
        elif(self.setup == False):
            if main_command == 'setup':
                # temp spectrum setup
                self.setup = True
                self.setTrig(False)
                self.setSpectrumAcquisition(40e6, 801)
                self.dataThread = Thread(target=self.start)
                self.dataThread.start()
            elif main_command == 'start':
                self.dataThread = Thread(target=self.start)
                self.dataThread.start()
        else:
            if main_command.split(' ')[0] == 'frequency':
                self.setCenterFrequency(float(main_command.split(' ')[1]))
            if main_command.split(' ')[0] == 'reflevel':
                self.setReferenceLevel(float(main_command.split(' ')[1]))
            if main_command.split(' ')[0] == 'trigger':
                self.triggerCommand = main_command
            if main_command.split(' ')[0] == 'data':
                self.dataCommand = main_command


        split_command = command.split('|')
        next_command = None
        if( len(split_command) > 2 ):
            next_command = split_command[1] + '|'
            for i in range(2,len(split_command)-1):
                next_command = next_command + split_command[i] + '|'
            self.handleCommand(next_command)

    #once setup is finished, change the settings of the RSA
    def setSettings(self):
        # set trigger
        if self.triggerCommand != '':
            if self.triggerCommand.split(' ')[1] == 'p':
                self.setTrig(True)
                self.setPowerTrig(float(self.triggerCommand.split(' ')[2]))
            elif self.triggerCommand.split(' ')[1] == 't':
                self.setTrig(True)
                second = int(self.triggerCommand.split(' ')[2].split(':')[2])
                minute = int(self.triggerCommand.split(' ')[2].split(':')[1])
                hour = int(self.triggerCommand.split(' ')[2].split(':')[0])
                span = int(self.triggerCommand.split(' ')[3])
                self.setTimeTrig(hour, minute, second, span)
            elif self.triggerCommand.split(' ')[1] == 'e':
                self.setTrig(True)
                self.setExternalTrig()
            elif self.triggerCommand.split(' ')[1] == 'f':
                self.setTrig(False)

        # set data
        if self.dataCommand != '':
            if self.dataCommand.split(' ')[1] == 'dpx':  # d span minpow width time
                self.setDPXAcquisition(float(self.dataCommand.split(' ')[2]),
                                       float(self.dataCommand.split(' ')[3]),
                                       int(self.dataCommand.split(' ')[4]),
                                       float(self.dataCommand.split(' ')[5]))
            elif self.dataCommand.split(' ')[1] == 'spec':  # s span width
                self.setSpectrumAcquisition(float(self.dataCommand.split(' ')[2]),
                                            int(self.dataCommand.split(' ')[3]))
            elif self.dataCommand.split(' ')[1] == 'iq':  # i span time
                self.setIQAcquisition(float(self.dataCommand.split(' ')[2]),
                                      float(self.dataCommand.split(' ')[3]))

    #***SHOULD ONLY BE CREATED IN SEPERATE THREAD***
    #start sending requested data to the server
    def start(self):
        CH.err_check(self.rsa.DEVICE_Run())
        self.threadActive = True
        while( True ):

            if ( self.dataMode == 's' ):
                with self.frcond:
                    if (self.threadActive == False):
                        break
                    while(self.file_ready == False):
                        self.frcond.wait()
                    self.file_ready = False
                    if (self.threadActive == False):
                        break
                    trace, width = self.acquireSpectrumFrame()
                    spectrum_data = SpectrumGraphData(trace,width.value,self.centerFreq,self.dataSpan,self.refLevel)
                    CH.saveSpectrum("/temp_spec",spectrum_data)
                    self.sendSpectrum()
            elif ( self.dataMode == 'd' ):
                with self.frcond:
                    if (self.threadActive == False):
                        break
                    while(self.file_ready == False):
                        self.frcond.wait()
                    self.file_ready = False
                    if (self.threadActive == False):
                        break
                    bitmap, dpx_info = self.acquireDPXFrame()
                    dpx_data = DPXGraphData(bitmap, dpx_info.spectrumBitmapWidth, dpx_info.spectrumBitmapHeight,
                                            self.getCenterFrequency(), self.getDataSpan(), self.getReferenceLevel(),
                                            self.minLevel)
                    CH.saveDPX("/temp_dpx",dpx_data)
                    self.sendDPX()
            elif ( self.dataMode == 'i'):
                with self.frcond:
                    if (self.threadActive == False):
                        break
                    while(self.file_ready == False):
                        self.frcond.wait()
                    self.file_ready = False
                    if (self.threadActive == False):
                        break
                    i, q, length = self.acquireIQFrame()
                    samp_rate = c_double(0.0)
                    self.rsa.IQBLK_GetIQSampleRate(byref(samp_rate))
                    iq_data = IQGraphData(i,q,length,length*samp_rate.value,self.centerFreq,self.dataSpan,self.refLevel)
                    CH.saveIQ("/temp_iq",iq_data)
                    self.sendIQ()
        return

    #stop sending data
    def stop(self):
        with self.frcond:
            self.threadActive = False
            self.file_ready = True
            self.rsa.DEVICE_Stop()
            self.frcond.notify()

    #setting the different types of data aquisition
    #IQ DATA
    def setIQAcquisition( self, span, time ):
        self.dataMode = "i"
        self.rsa.IQBLK_SetIQBandwidth(c_double(span))
        self.dataSpan = span


        iqSampleRate = c_double(0)
        self.rsa.IQBLK_GetIQSampleRate(byref(iqSampleRate))
        self.rsa.IQBLK_SetIQRecordLength(c_int(int(iqSampleRate.value*time)))
        return True

    #Spectrum Data
    def setSpectrumAcquisition(self, span, width):
        self.dataMode = "s"
        CH.err_check(self.rsa.DPX_SetEnable(c_bool(False)))
        self.rsa.SPECTRUM_SetEnable(c_bool(True))

        self.rsa.SPECTRUM_SetDefault()
        specSet = Spectrum_Settings()
        self.rsa.SPECTRUM_GetSettings(byref(specSet))
        specSet.window = SpectrumWindows.SpectrumWindow_Kaiser
        specSet.verticalUnit = SpectrumVerticalUnits.SpectrumVerticalUnit_dBm
        specSet.span = span
        specSet.rbw = span/100.0
        specSet.traceLength = width
        self.rsa.SPECTRUM_SetSettings(specSet)
        return specSet

    #DPX Data
    def setDPXAcquisition( self, span, minPow, width, time):
        self.dataMode = "d"
        c_span = c_double(span)
        c_width = c_int(width)
        c_refLevel = c_double(0.0)
        CH.err_check(self.rsa.CONFIG_GetReferenceLevel(byref(c_refLevel)))
        c_minRBW = c_double(0.0)
        c_maxRBW = c_double(0.0)
        CH.err_check(self.rsa.DPX_GetRBWRange(c_span, byref(c_minRBW), byref(c_maxRBW)))
        c_rbw = c_double(span/100.0)
        c_minPow = c_double(minPow)
        self.minLevel = minPow
        c_time = c_double(time)

        self.dataSpan = span
        CH.err_check(self.rsa.SPECTRUM_SetEnable(c_bool(False)))
        CH.err_check(self.rsa.DPX_SetEnable(c_bool(True)))
        CH.err_check(self.rsa.DPX_SetParameters(c_span, c_rbw, c_width, c_int(1), VerticalUnitType.VerticalUnit_dBm,
                                                  c_refLevel, c_minPow, c_bool(False), c_time, self.triggerd))
        CH.err_check(self.rsa.DPX_Configure(c_bool(True), c_bool(False)))
        return True

    #Acquireing different types of data when RSA is triggered
    #Spectrum
    def acquireSpectrumFrame(self):
        ready = c_bool(False)
        specSet = Spectrum_Settings()
        CH.err_check(self.rsa.SPECTRUM_GetSettings(byref(specSet)))
        traceArray = c_float * specSet.traceLength
        traceData = traceArray()
        width = c_int(0)
        traceSelector = SpectrumTraces.SpectrumTrace1

        CH.err_check(self.rsa.SPECTRUM_AcquireTrace())
        while not ready.value:
            if (self.time != None):
                now = datetime.datetime.now().replace(microsecond=0)
                self.time = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                              datetime.datetime.now().day, self.time.hour, self.time.minute, self.time.second)
                if(self.time < now and self.time + self.timeSpan > now):
                    self.rsa.TRIG_ForceTrigger()
            CH.err_check(self.rsa.SPECTRUM_WaitForDataReady(c_int(100), byref(ready)))
        CH.err_check(self.rsa.SPECTRUM_GetTrace(traceSelector, specSet.traceLength, byref(traceData), byref(width)))
        return np.array(traceData), width

    #IQ
    def acquireIQFrame(self):
        ready = c_bool(False)
        recordLength = c_int(0)
        self.rsa.IQBLK_GetIQRecordLength(byref(recordLength))
        iqArray = c_float * recordLength.value
        iData = iqArray()
        qData = iqArray()
        outLength = 0
        self.rsa.IQBLK_AcquireIQData()
        while not ready.value:
            if (self.time != None):
                now = datetime.datetime.now().replace(microsecond=0)
                self.time = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                              datetime.datetime.now().day, self.time.hour, self.time.minute, self.time.second)
                if(self.time < now and self.time + self.timeSpan > now):
                    self.rsa.TRIG_ForceTrigger()
            self.rsa.IQBLK_WaitForIQDataReady(c_int(100), byref(ready))
        self.rsa.IQBLK_GetIQDataDeinterleaved(byref(iData), byref(qData),
                                         byref(c_int(outLength)), recordLength)

        return np.array(iData), np.array(qData), outLength

    #DPX
    def acquireDPXFrame(self):
        c_available = c_bool(False)
        c_ready = c_bool(False)
        dpxf = DPX_FrameBuffer()

        CH.err_check(self.rsa.DPX_Reset())

        while not c_available.value:
            CH.err_check(self.rsa.DPX_IsFrameBufferAvailable(byref(c_available)))
            while not c_ready.value:
                if (self.time != None):
                    now = datetime.datetime.now().replace(microsecond=0)
                    self.time = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month,
                                                  datetime.datetime.now().day, self.time.hour, self.time.minute,
                                                  self.time.second)
                    if (self.time < now and self.time + self.timeSpan > now):
                        self.rsa.TRIG_ForceTrigger()
                CH.err_check(self.rsa.DPX_WaitForDataReady(c_int(100), byref(c_ready)))
        CH.err_check(self.rsa.DPX_GetFrameBuffer(byref(dpxf)))
        CH.err_check(self.rsa.DPX_FinishFrameBuffer())
        bitmap = np.fromiter(dpxf.spectrumBitmap, dtype=np.float, count=dpxf.spectrumBitmapSize)
        return bitmap, dpxf

    #Sending data back to server
    #Spectrum
    def sendSpectrum(self):
        with self.crcond:
            tosend = open(DATA_PATH + "/temp_spec" + SPEC_DATA_FILE_EXTENSION, "rb")
            tsb = tosend.read(1024)
            while(tsb):
                while(self.chunk_ready == False):
                    self.crcond.wait()
                self.chunk_ready = False
                self.s.send(tsb)
                tsb = tosend.read(1024)
            while (self.chunk_ready == False):
                self.crcond.wait()
            self.s.send(b"done")
            tosend.close()

    #DPX
    def sendDPX(self):
        with self.crcond:
            tosend = open(DATA_PATH + "/temp_dpx" + DPX_DATA_FILE_EXTENSION, "rb")
            tsb = tosend.read(1024)
            while(tsb):
                while(self.chunk_ready == False):
                    self.crcond.wait()
                self.chunk_ready = False
                self.s.send(tsb)
                tsb = tosend.read(1024)
            while (self.chunk_ready == False):
                self.crcond.wait()
            self.s.send(b"done")
            tosend.close()

    #IQ
    def sendIQ(self):
        with self.crcond:
            tosend = open(DATA_PATH + "/temp_iq" + IQ_DATA_FILE_EXTENSION, "rb")
            tsb = tosend.read(1024)
            while(tsb):
                while(self.chunk_ready == False):
                    self.crcond.wait()
                self.chunk_ready = False
                self.s.send(tsb)
                tsb = tosend.read(1024)
            while (self.chunk_ready == False):
                self.crcond.wait()
            self.s.send(b"done")
            tosend.close()


    def setCenterFrequency( self, freq ):
        c_freq = c_double(freq)
        self.centerFreq = freq
        CH.err_check(self.rsa.CONFIG_SetCenterFreq(c_freq))
        return True

    def getCenterFrequency(self):
        return self.centerFreq

    def setReferenceLevel( self, refLevel ):
        c_refLevel = c_double(refLevel)
        self.refLevel = refLevel
        CH.err_check(self.rsa.CONFIG_SetReferenceLevel(c_refLevel))
        return True

    def getReferenceLevel(self):
        return self.refLevel

    def getDataSpan(self):
        return self.dataSpan

    def setTrig(self, trig):
        if trig:
            CH.err_check(self.rsa.TRIG_SetTriggerMode(TriggerMode.triggered))
            self.triggerd = True
        else:
            CH.err_check(self.rsa.TRIG_SetTriggerMode(TriggerMode.freeRun))
            self.triggerd = False
            self.time = None

    def setPowerTrig(self, trigLevel):
        self.time = None
        c_trigLevel = c_double(trigLevel)
        CH.err_check(self.rsa.TRIG_SetTriggerSource(TriggerSource.TriggerSourceIFPowerLevel))
        CH.err_check(self.rsa.TRIG_SetIFPowerTriggerLevel(c_trigLevel))
        CH.err_check(self.rsa.TRIG_SetTriggerPositionPercent(c_double(50)))

    def setTimeTrig(self, hour, minute, second, timeSpan):
        self.time = datetime.datetime(datetime.datetime.now().year,datetime.datetime.now().month,datetime.datetime.now().day,hour,minute,second)
        self.timeSpan = datetime.timedelta(0,timeSpan)
        CH.err_check(self.rsa.TRIG_SetTriggerSource(TriggerSource.TriggerSourceExternal))
        CH.err_check(self.rsa.TRIG_SetTriggerPositionPercent(c_double(50)))
        #set time trigger

    def setExternalTrig(self):
        self.time = None
        CH.err_check(self.rsa.TRIG_SetTriggerSource(TriggerSource.TriggerSourceExternal))
        CH.err_check(self.rsa.TRIG_SetTriggerPositionPercent(c_double(50)))

#MAIN

Client = Client() #create a client

while True: #send client commands from the server
    main_command = Client.s.recv(1024)
    Client.handleCommand(main_command.decode("utf-8"))



