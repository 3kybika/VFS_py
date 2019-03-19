
from winfspy import (FILE_ATTRIBUTE, CREATE_FILE_CREATE_OPTIONS)
from defines import container_path
import os 
from winfspy.plumbing.winstuff import filetime_now, SecurityDescriptor

from defines import container_path

class BaseFileObj:
    @property
    def name(self):
        return self.path.name

    def __init__(self, path, root_path):
        self.path = path
        self.root_path = str(root_path)
        
        now = filetime_now()
        self.creation_time = now
        self.last_access_time = now
        self.last_write_time = now
        self.change_time = now
        self.index_number = 0

        self.security_descriptor = SecurityDescriptor("O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;FA;;;WD)")

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

    def getNormPath(self):
        return os.path.normpath(self.root_path + '/' + str(self.path))