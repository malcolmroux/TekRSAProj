

def setIQAquisition(self, bandwidth, recordLength):
    c_bandwidth = c_double(bandwidth * 1.4)
    c_recordLength = c_int(int(bandwidth * 1.4 * recordLength))

    self.err_check(self.rsa.IQBLK_SetIQBandwidth(c_bandwidth))
    self.err_check(self.rsa.IQBLK_SetIQRecordLength(c_recordLength))

    return True


def acquireIQBlock(self):
    c_ready = c_bool(False)

    IQArray = c_float * self.c_recordLength
    iData = IQArray()
    qData = IQArray()

    self.err_check(self.rsa.DEVICE_Run())
    self.err_check(self.rsa.DPX_Reset())

    while not c_ready.value:
        self.errCheck(self.rsa.IQBLK_WaitForIQDataReady(c_int(100), byref(c_ready)))

    print('triggered')
    self.err_check(self.rsa.IQBLK_GetIQDataDeinterleaved(byref(iData), byref(qData),
                                                         byref(c_int(0)), c_int(self.c_recordLength)))
    self.err_check(self.rsa.DEVICE_Stop())

    return np.array(iData) + 1j * np.array(qData)


def saveIQ(self, dst_path, filename, graph_data):
    if not dst_path.is_dir()
        # the given directory doesn't exist
        return False
    file_location = dst_path / Path(filename + GRAPH_DATA_FILE_EXTENSION)

    with open(file_location, "wb") as file:
        np.save(filename, graph_data.IQ_graph)
        pickle.dump(graph_data.iData, file)
        pickle.dump(graph_data.qData, file)
        pickle.dump(graph_data.bandwidth, file)
        pickle.dump(graph_data.center_frequency, file)
        pickle.dump(graph_data.record_length, file)
        pickle.dump(graph_data.ref_level, file)
        pickle.dump(graph_data.sampleRate, file)
    return True

class IQGraphData:

    def __init__(self, iData, qData, bandwidth, center_frequency, record_length, ref_level, sample_rate):
        # The numpy array containing the I portion of IQ data.
        self.iData = iData
        # The numpy array containing the Q portion of IQ data.
        self.qData = qData
        #the bandwidth of the IQ graph
        self.bandwidth = bandwidth
        # The center frequency in Hz that the RSA was set to when reading the IQ data.
        self.center_frequency = center_frequency
        # The span in Hz that the RSA was set to when reading the IQ data.
        self.record_length = record_length
        # The lower bound on power level is always the reference level - 100 dBm.
        self.ref_level = ref_level
        # the sample rate of the IQ data received
        self.sample_rate = sample_rate
