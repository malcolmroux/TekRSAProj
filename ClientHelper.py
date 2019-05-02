import numpy as np
import Client
from RSA_API import *
import pickle

""""Helper meathods for Client"""

#checks error message from RSA API
def err_check(self, rs):
    if ReturnStatus(rs) != ReturnStatus.noError:
        raise RSAError(ReturnStatus(rs).name)

#Save data to temp files
#Spectrum
def saveSpectrum(filename, graph_data):

    file = open(Client.DATA_PATH + filename + Client.SPEC_DATA_FILE_EXTENSION, "wb+")
    np.save(file, graph_data.trace)
    pickle.dump(graph_data.width, file)
    pickle.dump(graph_data.center_frequency, file)
    pickle.dump(graph_data.span, file)
    pickle.dump(graph_data.ref_level, file)

#DPX
def saveDPX(filename, graph_data):
    file = open(Client.DATA_PATH + filename + Client.DPX_DATA_FILE_EXTENSION, "wb+")
    np.save(file, graph_data.DPX_bitmap)
    pickle.dump(graph_data.bitmap_width, file)
    pickle.dump(graph_data.bitmap_height, file)
    pickle.dump(graph_data.center_frequency, file)
    pickle.dump(graph_data.span, file)
    pickle.dump(graph_data.ref_level, file)
    pickle.dump(graph_data.min_level, file)

#IQ
def saveIQ(filename, graph_data):
    file = open(Client.DATA_PATH + filename + Client.IQ_DATA_FILE_EXTENSION, "wb+")
    np.save(file, graph_data.i)
    np.save(file, graph_data.q)
    pickle.dump(graph_data.length, file)
    pickle.dump(graph_data.time, file)
    pickle.dump(graph_data.center_frequency, file)
    pickle.dump(graph_data.span, file)