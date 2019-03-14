from .BaseFileObj import BaseFileObj 

from winfspy import FILE_ATTRIBUTE

import defines
from fsCrypto import align_offset_length, encrypt_file_blocks, decrypt_file_blocks

class FileObj(BaseFileObj):
    def __init__(self, path, data=b''):
        super().__init__(path)
        self.data = bytearray(data)
        self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL

    @property
    def file_size(self):
        return len(self.data)

    @property
    def allocation_size(self):
        if len(self.data) % 4096 == 0:
            return len(self.data)
        else:
            return ((len(self.data) // 4096) + 1) * 4096

    def save(self):
        print('[WRITE]')

        offset = 0
        lenght = self.allocation_size

        offset_al, lenght_al = align_offset_length(offset, lenght)

        try:
            source = self.read(lenght, offset)
        except:
            source = b''

        buf_al = source[:offset - offset_al] + self.data

        if lenght_al - lenght - (offset - offset_al) > 0:
            buf_al += source[-(lenght_al - lenght - (offset - offset_al)):]

        buf_enc = encrypt_file_blocks(offset_al, defines.AES_KEY, buf_al)
    
        f = open(defines.container_path + str(self.path), "wb+")
        f.seek(offset_al)
        f.write(buf_enc)