
from ctypes import *
import os
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
from RSA_API import *
import pickle
from pathlib import Path

GRAPH_DATA_FILE_EXTENSION = ".dsi"

#Sets directory to RSA API
os.chdir("C:\Tektronix\RSA_API\lib\\x64")
r = os.getcwd()
#Makes sure directory is correct
print("Current directory is %s" % r)


class RSAController(object):

    def __init__(self):
        self.rsa = cdll.LoadLibrary("RSA_API.dll")
        self.refLevel = 0.0
        self.minLevel = -100.0
        self.centerFreq = 1.5e9
        self.dataSpan = 40.0e6
        self.search_connect()

    def search_connect( self ):
        numFound = c_int(0)
        intArray = c_int * DEVSRCH_MAX_NUM_DEVICES
        deviceIDs = intArray()
        deviceSerial = create_string_buffer(DEVSRCH_SERIAL_MAX_STRLEN)
        deviceType = create_string_buffer(DEVSRCH_TYPE_MAX_STRLEN)
        apiVersion = create_string_buffer(DEVINFO_MAX_STRLEN)

        self.err_check(self.rsa.DEVICE_GetAPIVersion(apiVersion))
        print('API Version {}'.format(apiVersion.value.decode()))

        self.err_check(self.rsa.DEVICE_Search(byref(numFound), deviceIDs,
                                    deviceSerial, deviceType))

        if numFound.value < 1:
            # rsa.DEVICE_Reset(c_int(0))
            print('No instruments found. Exiting script.')
            exit()
        elif numFound.value == 1:
            print('One device found.')
            print('Device type: {}'.format(deviceType.value.decode()))
            print('Device serial number: {}'.format(deviceSerial.value.decode()))
            self.err_check(self.rsa.DEVICE_Connect(deviceIDs[0]))
        else:
            # corner case
            print('2 or more instruments found. Enumerating instruments, please wait.')
            for inst in deviceIDs:
                self.err_check(self.rsa.DEVICE_Connect(inst))
                self.err_check(self.rsa.DEVICE_GetSerialNumber(deviceSerial))
                self.err_check(self.rsa.DEVICE_GetNomenclature(deviceType))
                print('Device {}'.format(inst))
                print('Device Type: {}'.format(deviceType.value))
                print('Device serial number: {}'.format(deviceSerial.value))
                self.err_check(self.rsa.DEVICE_Disconnect())
            # note: the API can only currently access one at a time
            selection = 1024
            while (selection > numFound.value - 1) or (selection < 0):
                selection = int(input('Select device between 0 and {}\n> '.format(numFound.value - 1)))
            self.err_check(self.rsa.DEVICE_Connect(deviceIDs[selection]))
            self.err_check(self.rsa.CONFIG_Preset())

    def err_check(self, rs):
        if ReturnStatus(rs) != ReturnStatus.noError:
            raise RSAError(ReturnStatus(rs).name)

    def setCenterFrequency( self, freq ):
        c_freq = c_double(freq)
        self.centerFreq = freq
        self.err_check(self.rsa.CONFIG_SetCenterFreq(c_freq))
        return True

    def getCenterFrequency(self):
        return self.centerFreq

    def setReferenceLevel( self, refLevel ):
        c_refLevel = c_double(refLevel)
        self.refLevel = refLevel
        self.err_check(self.rsa.CONFIG_SetReferenceLevel(c_refLevel))
        return True

    def getReferenceLevel(self):
        return self.refLevel

    def getDataSpan(self):
        return self.dataSpan

    #under construction
    def setIQAquisition( self, bandwidth, time ):
        c_bandwidth = c_double(bandwidth)
        c_recordLength = c_int(int( bandwidth*1.4*time ))
        self.err_check(self.rsa.IQBLK_SetIQBandwidth(c_bandwidth))
        self.err_check(self.rsa.IQBLK_SetIQRecordLength(c_recordLength))
        return True

    def setDPXAquisition( self, span, minPow, width, time ):
        c_span = c_double(span)
        c_width = c_int(width)
        c_refLevel = c_double(0.0)
        self.err_check(self.rsa.CONFIG_GetReferenceLevel(byref(c_refLevel)))
        c_minRBW = c_double(0.0)
        c_maxRBW = c_double(0.0)
        self.err_check(self.rsa.DPX_GetRBWRange(c_span, byref(c_minRBW), byref(c_maxRBW)))
        c_rbw = c_double(span/100.0)
        c_minPow = c_double(minPow)
        c_time = c_double(time)

        self.dataSpan = span
        self.err_check(self.rsa.DPX_SetEnable(c_bool(True)))
        #self.err_check(self.rsa.DPX_SetParameters(c_double(40e6), c_double(100e3), c_int(801), c_int(1),
                                                  #VerticalUnitType.VerticalUnit_dBm, c_double(-30), c_double(-130),
                                                  #c_bool(False), c_double(1.0), c_bool(False)))
        self.err_check(self.rsa.DPX_SetParameters(c_span, c_rbw, c_width, c_int(1), VerticalUnitType.VerticalUnit_dBm,
                                                  c_refLevel, c_minPow, c_bool(False), c_time, c_bool(False)))
        self.err_check(self.rsa.DPX_Configure(c_bool(True), c_bool(False)))
        return True

    def setTrig(self, trig):
        if trig:
            self.err_check(self.rsa.TRIG_SetTriggerMode(TriggerMode.triggered))
        else:
            self.err_check(self.rsa.TRIG_SetTriggerMode(TriggerMode.freeRun))

    def acquireDPXFrame(self):
        c_available = c_bool(False)
        c_ready = c_bool(False)
        dpxf = DPX_FrameBuffer()

        self.err_check(self.rsa.DEVICE_Run())
        self.err_check(self.rsa.DPX_Reset())

        while not c_available.value:
            self.err_check(self.rsa.DPX_IsFrameBufferAvailable(byref(c_available)))
            while not c_ready.value:
                print("here")
                self.err_check(self.rsa.DPX_WaitForDataReady(c_int(100), byref(c_ready)))
        self.err_check(self.rsa.DPX_GetFrameBuffer(byref(dpxf)))
        self.err_check(self.rsa.DPX_FinishFrameBuffer())
        self.err_check(self.rsa.DEVICE_Stop())
        return dpxf

    def saveDPX(self, dst_path, filename, graph_data):
        if not dst_path.is_dir():
            # The given directory doesn't exist.
            return False
        file_location = dst_path / Path(filename + GRAPH_DATA_FILE_EXTENSION)
        with open(file_location, "wb") as file:
            np.save(file, graph_data.DPX_bitmap)
            pickle.dump(graph_data.bitmap_width, file)
            pickle.dump(graph_data.bitmap_height, file)
            pickle.dump(graph_data.center_frequency, file)
            pickle.dump(graph_data.span, file)
            pickle.dump(graph_data.ref_level, file)
        return True


class DPXGraphData:

    def __init__(self, bitmap, bitmap_width, bitmap_height, center_frequency, span, ref_level):
        # The numpy array containing the DPX bitmap.
        self.DPX_bitmap = bitmap
        # The number of columns in the bitmap.
        self.bitmap_width = bitmap_width
        # The number of rows in the bitmap.
        self.bitmap_height = bitmap_height
        # The center frequency in Hz that the RSA was set to when reading the DPX data.
        self.center_frequency = center_frequency
        # The span in Hz that the RSA was set to when reading the DPX data.
        self.span = span
        # The upper bound on power level (the y-axis) that was graphed in dBm.
        # The lower bound on power level is always the reference level - 100 dBm.
        self.ref_level = ref_level


RSAController = RSAController()
RSAController.setReferenceLevel(-25.0)
RSAController.setCenterFrequency(92.3e6)
RSAController.setDPXAquisition(500000.0,-125,800,1.0)
RSAController.setTrig(False)
dpx_data_c = RSAController.acquireDPXFrame()
numpy_bitmap = np.fromiter(dpx_data_c.spectrumBitmap, dtype=np.float, count=dpx_data_c.spectrumBitmapSize)
dpx_data = DPXGraphData(numpy_bitmap, dpx_data_c.spectrumBitmapWidth, dpx_data_c.spectrumBitmapHeight,
                        RSAController.getCenterFrequency(), RSAController.getDataSpan(), RSAController.getReferenceLevel())

RSAController.saveDPX(Path("C:/Users/thema/OneDrive/Documents/Malcolm's_Things/Fall 2018"), "test", dpx_data)

print("success!")


