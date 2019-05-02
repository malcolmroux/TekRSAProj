class DPXGraphData:

    def __init__(self, bitmap, bitmap_width, bitmap_height, center_frequency, span, ref_level):
        self.DPX_bitmap = bitmap
        self.bitmap_width = bitmap_width
        self.bitmap_height = bitmap_height
        self.center_frequency = center_frequency
        self.span = span
        self.ref_level = ref_level
        self.min_level = ref_level