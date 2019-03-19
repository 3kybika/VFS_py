from .BaseFileObj import BaseFileObj 

from winfspy import FILE_ATTRIBUTE
import win32con, win32api, os
import ctypes


class FolderObj(BaseFileObj):
    def __init__(self, path, root_path):
        super().__init__(path, root_path)
        self.file_size = 4096
        self.allocation_size = 4096
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY

    def isEmpty():
        return not os.listdir(
            os.path.normpath(container_path + '/' + self.path)
        )