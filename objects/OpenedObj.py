from .BaseFileObj import BaseFileObj 
from fsCrypto import align_offset_length, encrypt_file_blocks, decrypt_file_blocks
import os
import defines
from winfspy.plumbing.winstuff import filetime_now

class OpenedObj:
    def __init__(self, file_obj):
        self.file_obj = file_obj
        file_obj.open()