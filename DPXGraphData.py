
# This class stores the data necessary to analyze and graph DPX bitmaps
# that were read from the spectrum analyzer.
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




        # TODO: email Malcolm this class code, and the file saving and loading
        # code. Also, write up a formal document specifying the data stored
        # in this class, and the sequence that each variable is saved to
        # files/loaded from files.
