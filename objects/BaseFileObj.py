from winfspy.plumbing.winstuff import filetime_now, security_descriptor_factory

from winfspy import (FILE_ATTRIBUTE, CREATE_FILE_CREATE_OPTIONS)

from defines import container_path
import os 

class BaseFileObj:
    def __init__(self, path):
        self.path = os.path.normpath(path)
        now = filetime_now()
        self.creation_time = now
        self.last_access_time = now
        self.last_write_time = now
        self.change_time = now
        self.index_number = 0
 
        self.attributes = None

        self.security_descriptor, self.security_descriptor_size = security_descriptor_factory("O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;WD)")

    @property
    def name(self):
        return self.path.name

    #@property
    #def attributes(self): 
        #return FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL
        #return os.stat(self.path)
    
    def getNormPath(self):
        return os.path.normpath(container_path + '/' + self.path)

    @property
    def allocation_size(self):
        return os.stat(self.getNormPath()).st_size

    @property
    def file_size(self):
        return  os.path.getsize(self.getNormPath())

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

