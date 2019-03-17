from .BaseFileObj import BaseFileObj 

from winfspy import FILE_ATTRIBUTE
import win32con, win32api, os
import ctypes


class FolderObj(BaseFileObj):
    def __init__(
        self, 
        path, 
        createFolder = False, 
        attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY    
    ):
        super().__init__(path)  
        if (not os.path.isdir(self.getNormPath()) and not createFolder and not path == '\\'):
            print("error dir:", self.getNormPath())
            raise Exception()
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY

        if (createFolder):
            os.mkdir(self.getNormPath())
            win32api.SetFileAttributes(self.getNormPath(), attributes)
            #self.attributes = attributes
        #else:
            #self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY #os.stat(self.path)
            #ToDo
            #self.creation_time = now
            #self.last_access_time = now
            #self.last_write_time = now
            #self.change_time = now
            #self.index_number = 0

        
