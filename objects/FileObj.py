from .BaseFileObj import BaseFileObj 
from winfspy import FILE_ATTRIBUTE
from fsCrypto import align_offset_length, encrypt_file_blocks, decrypt_file_blocks
import win32con, win32api, os

import defines

class FileObj(BaseFileObj):
    def __init__(
        self, 
        path, 
        createfile = False, 
        attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL
    ):
        super().__init__(str(path))
        if (not os.path.isfile(self.getNormPath()) and not createfile):
            print("error file:", self.getNormPath(),"error file:", self.path)
            raise Exception()
           
        if (createfile):
            file = open(self.getNormPath(), "wb+")
            win32api.SetFileAttributes(file, attributes)
            file.close()
            self.attributes = attributes
        else:
            self.attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL#os.stat(self.getNormPath())
            #ToDo
            #self.creation_time = now
            #self.last_access_time = now
            #self.last_write_time = now
            #self.change_time = now
            #self.index_number = 0

    def __str__(self):
        return self.path + " : " + "FileObj" 

    def setAttributes(self, attributes):
        file = open(self.getNormPath(), "wb")
        win32api.SetFileAttributes(file, attributes)
        file.close()

    def read(self, offset, length):
        print('[READ]')

        offset_al, lenght_al = align_offset_length(offset, length)
        
        f = open(self.getNormPath(), "rb")
        f.seek(offset_al)
        data = f.read(lenght_al)

        if (len(data) == 0) :
            return b''
        
        data_dec = decrypt_file_blocks(offset_al, defines.AES_KEY, data)
        return data_dec[offset - offset_al: length]
        
    
    def write(self, offset, length, buf, write_to_end_of_file):
        print('[WRITE]')

        length = len(buf)
        offset_al, lenght_al = align_offset_length(offset, length)
        print('buf', buf)
        try:
            source = self.read(offset_al, lenght_al)
        except:
            source = b''

        source = source[:offset - offset_al] + buf #+ source[length + offset - offset_al:]

        buf_enc = encrypt_file_blocks(offset_al, defines.AES_KEY, source)
   
        fh = os.open(self.getNormPath(), os.O_WRONLY)
        os.lseek(fh, offset_al, os.SEEK_SET)
        os.write(fh, buf_enc)
        os.ftruncate(fh, offset_al + len(buf_enc))
            
        
        # 
        #     print('truncate file:')
        #     os.truncate(fh, offset_al + length) 
         
