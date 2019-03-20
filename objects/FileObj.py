from .BaseFileObj import BaseFileObj 
from winfspy import FILE_ATTRIBUTE
from fsCrypto import align_offset_length, encrypt_file_blocks, decrypt_file_blocks
import win32con, win32api, os

import defines

class FileObj(BaseFileObj):
    def __init__(self, path, creating = False):
        super().__init__(path)
        if creating:
            self.create()
        self.data = self.read(0, os.path.getsize(self.getNormPath()))
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL
 
    def create(self):
        file = open(self.getNormPath(), "wb+")
        file.close()

    @property
    def file_size(self):
        #return os.stat(self.getNormPath()).st_size
        return len(self.data)

    @property
    def allocation_size(self):
        if len(self.data) % 4096 == 0:
            return len(self.data)
        else:
            return ((len(self.data) // 4096) + 1) * 4096

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

    def save(self):
        print('[SAVE]')
        buf_enc = encrypt_file_blocks(0, defines.AES_KEY, self.data)
    
        f = open(self.getNormPath(), "wb+")
        #f.seek(offset_al)
        f.write(buf_enc)

    def write(
        self,
        file_context,
        buffer,
        offset,
        write_to_end_of_file,
        constrained_io
    ):
        print('[WRITE]')
        length = len(buffer)

        if constrained_io:
           if offset >= len(self.data):
               return 0
           end_offset = min(len(self.data), offset + length)
           transferred_length = end_offset - offset
           # self.data[offset:end_offset] = buffer[:transferred_length]
           self.data = self.data[:offset] + buffer[:transferred_length] +  self.data[end_offset:]
           self.save()
           return transferred_length

        else:
           if write_to_end_of_file:
               offset = len(self.data)
           end_offset = offset + length
           self.data = self.data[:offset] + buffer + self.data[end_offset:]
           #self.data[offset:end_offset] = buffer
           self.save()
           return length