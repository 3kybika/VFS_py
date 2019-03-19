from .BaseFileObj import BaseFileObj 
from winfspy import FILE_ATTRIBUTE
from fsCrypto import align_offset_length, encrypt_file_blocks, decrypt_file_blocks
import win32con, win32api, os

import defines

class FileObj(BaseFileObj):
    def __init__(self, path, root_path):
        super().__init__(path, root_path)
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL
        self.data = b''
    @property
    def file_size(self):
        return os.path.getsize(self.getNormPath())

    @property
    def allocation_size(self):
        if self.file_size % 4096 == 0:
            return self.file_size
        else:
            return ((self.file_size // 4096) + 1) * 4096

    def read(self, offset, length):
        print('[READ]')
        offset_al, lenght_al = align_offset_length(offset, length)
        
        f = open(self.getNormPath(), "rb")
        f.seek(offset_al)
        data = f.read(lenght_al)

        if (len(data) == 0) :
            return b''
        
        data_dec = decrypt_file_blocks(offset_al, defines.AES_KEY, data)
        return data_dec[offset_al-offset:offset_al-offset+length]

    def save(self, data):
        print('[SAVE]')
        buf_enc = encrypt_file_blocks(0, defines.AES_KEY, data)
    
        f = open(self.getNormPath(), "wb+")
        #f.seek(offset_al)
        f.write(buf_enc)

    def writing(
        self,
        file_context,
        buffer,
        offset,
        write_to_end_of_file,
        constrained_io
    ):
        print('[WRITE]')
        length = len(buffer)

        offset = 0
        length = os.stat(self.getNormPath()).st_size
        data = self.read(offset, length)

        if constrained_io:
            if offset >= len(data):
                return 0
            end_offset = min(len(data), offset + length)
           
            transferred_length = end_offset - offset
            data = data[:offset] + buffer[:transferred_length] +  data[end_offset:]
            self.save(data)
            return transferred_length

        else:
            if write_to_end_of_file:
                offset = len(data)
            end_offset = offset + length
            data = data[:offset] + buffer + data[end_offset:]
            self.save(data)
            return length