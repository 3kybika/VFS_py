from .BaseFileObj import BaseFileObj 

from winfspy import FILE_ATTRIBUTE
import win32con, win32api, os
import ctypes


class FolderObj(BaseFileObj):
    def __init__(self, path, file_attributes = None, creating =  False):
        if not file_attributes and creating:
            file_attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY
        super().__init__(path, file_attributes, creating)

    
    def create(self):
        os.mkdir(self.getNormPath())
        #win32api.SetFileAttributes(self.getNormPath(), self.attributes)
    
    def open(self):
        pass
        
    def close(self):
        pass
        
    @property
    def file_size(self):
        return self.getSize(self.path)

    @property
    def allocation_size(self):
        if self.file_size % 4096 == 0:
            return self.file_size
        else:
            return ((self.file_size // 4096) + 1) * 4096

    def getSize(self, path = "/"):
        total_size = os.path.getsize(self.getNormPath(path))
        for item in os.listdir(self.getNormPath(path)):
            full_path = self.getNormPath(path + '/' + item)
            cur_file_path = os.path.normpath(path + '/' + item)
            if os.path.isfile(full_path):
                total_size += os.path.getsize(full_path)
            elif os.path.isdir(full_path):
                total_size += self.getSize(cur_file_path)
        return total_size

    def isEmpty(self):
        return not os.listdir(
            self.getNormPath()
        )

        #ToDo renaming removing