class FramelibExecption(Exception):
    """Base class for framelib exceptions"""


class PhotoAlbumException(FramelibExecption):
    """Exception for problems accessing photo albums"""


class PhotoImageException(FramelibExecption):
    """Exception for accessing individual photos"""
