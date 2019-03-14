from .BaseFileObj import BaseFileObj 

from winfspy import FILE_ATTRIBUTE

class FolderObj(BaseFileObj):
    def __init__(self, path):
        super().__init__(path)
        self.file_size = 4096
        self.allocation_size = 4096
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_DIRECTORY
