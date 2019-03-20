from .BaseFileObj import BaseFileObj 

from winfspy import FILE_ATTRIBUTE
import win32con, win32api, os
import ctypes


class FolderObj(BaseFileObj):
    def __init__(self, path, creating =  False):
        super().__init__(path)
        if creating:
            self.create()
        self.file_size = 4096
        self.allocation_size = 4096
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY
    
    def create(self):
        os.mkdir(self.getNormPath())
    
    
    def isEmpty(self):
        return not os.listdir(
            self.getNormPath()
        )

        #ToDo renaming removing