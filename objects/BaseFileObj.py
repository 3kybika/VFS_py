
from winfspy import (FILE_ATTRIBUTE, CREATE_FILE_CREATE_OPTIONS)
from defines import container_path
import win32con, win32api, os
from winfspy.plumbing.winstuff import filetime_now, SecurityDescriptor, dt_to_filetime
import time
from defines import container_path
from time import mktime
from datetime import datetime

class BaseFileObj:
    def __init__(self, path, file_attributes, creating):
        self.path = str(path)
        self.root_path = str(container_path)

        self.attributes = file_attributes
        if creating:
            self.create()
        if (self.attributes == None):
            self.attributes = win32api.GetFileAttributes(self.getNormPath())
            print("self.attributes", self.attributes)

        stat = os.stat(self.getNormPath())

        self.creation_time = self.getFiletime((stat.st_ctime))
        self.last_access_time = self.getFiletime((stat.st_atime))
        self.last_write_time = self.getFiletime((stat.st_mtime))
        self.change_time = max(self.getFiletime((stat.st_mtime)), self.getFiletime((stat.st_ctime)))
        
        self.index_number = 0

        self.security_descriptor = SecurityDescriptor("O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;WD)")

    def getFiletime(self, time):
        return dt_to_filetime(datetime.fromtimestamp(time))

    def getNormPath(self, path = None):
        if path == None:
            path = self.path
        return os.path.normpath(self.root_path + '/' + str(path))

    @property
    def name(self):
        return self.path.name

    def create(self):
        raise NotImplementedError()

    def remove(self):
        os.remove(self.getNormPath())
    
    def rename(self, new_file_name):
        old_path = self.getNormPath()
        self.path = new_file_name
        print("renaming:", old_path, "in", self.getNormPath())
        os.rename(old_path, self.getNormPath())
        
    def get_file_info(self):
        return {
            'file_attributes': self.attributes,
            'allocation_size': self.allocation_size,
            'file_size': self.file_size,
            'creation_time': self.creation_time,
            'last_access_time': self.last_access_time,
            'last_write_time': self.last_write_time,
            'change_time': self.change_time,
            'index_number': self.index_number,
        }