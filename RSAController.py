import os
from RSA_API import *

#Sets directory to RSA API
os.chdir(r"C:\Tektronix\RSA_API\lib\x64")
r = os.getcwd()
#Makes sure directory is correct
print("Current directory is %s" % r)


class RSAController(object):

    def __init__(self):
        self.rsa = WinDLL("C:/Tektronix/RSA_API/lib/x64/RSA_API.dll")

    def search_connect( self ):
        #Search and Connect Variables
        numFound = c_int(0)
        intArray = c_int*10
        deviceIDs = intArray()
        deviceSerial = create_string_buffer(8)
        deviceType = create_string_buffer(8)
        apiVersion = create_string_buffer(16)


        #Get API version
        self.rsa.DEVICE_GetAPIVersion(apiVersion)
        print('API Version {}'.format(apiVersion.value.decode()))

        #Searching for Device
        ret = self.rsa.DEVICE_Search(byref(numFound), deviceIDs, deviceSerial, deviceType)
        if ret != 0:
                print('Error in Search: ' +str(ret))
                exit()
        if numFound.value < 1:
                print('No rsa Devices found')
                exit()
        elif numFound.value == 1:
                print('One device found.')
                ret = self.rsa.DEVICE_Connect(deviceIDs[0])
                print('Device Connected')
                self.rsa.CONFIG_preset()
                return
                if ret != 0:
                        print('Error in connecting: ' + str(ret))

        else:
                print('2 or more instruments found.')
                exit()

    def setCenterFrequency( self, freq ):
        c_freq = c_double(freq)
        self.rsa.CONFIG_SetCenterFreq(c_freq)
        return True

    def setReferenceLevel( self, refLevel ):
        c_refLevel = c_double(refLevel)
        self.rsa.CONFIG_SetReferenceLevel(c_refLevel)
        return True

    #under construction
    def setIQAquisition( self, bandwidth, time ):
        c_bandwidth = c_double(bandwidth)
        c_recordLength = c_int(int( bandwidth*1.4*time ))
        self.rsa.IQBLK_SetIQBandwidth(c_bandwidth)
        self.rsa.IQBLK_SetIQRecordLength(c_recordLength)
        return True

    def setDPXAquisition( self, span, minPow, width, time ):
        self.rsa.DPX_SetEnable(c_bool(True))
        c_span = c_double(span)
        c_width = c_double(width)
        c_refLevel = c_double(0.0)
        self.rsa.CONFIG_getReferenceLevel(byref(c_refLevel))
        c_minRBW = c_double(0.0)
        c_maxRBW = c_double(0.0)
        self.rsa.DPX_GetRBWRange(c_span, byref(c_minRBW), byref(c_maxRBW))
        c_rbw = c_double(span/100.0)
        c_minPow = c_double(minPow)
        c_time = c_double(time)
        self.rsa.DPX_SetParameters(c_span, c_rbw, c_width, c_int(1), VerticalUnitType.VerticalUnit_dBm, c_refLevel,
                                   c_minPow, c_bool(False), c_time, c_bool(True))
        self.rsa.DPX_Configure(c_bool(False), c_bool(False))
        return True


RSAController = RSAController()
RSAController.search_connect()
RSAController.setReferenceLevel(-25.0)
RSAController.setCenterFrequency(92.3e6)
RSAController.setDPXAquisition(500e3,-125,801,,)

