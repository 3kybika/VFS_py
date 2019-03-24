from .BaseFileObj import BaseFileObj 
from winfspy import FILE_ATTRIBUTE
from fsCrypto import align_offset_length, encrypt_file_blocks, decrypt_file_blocks
import win32con, win32api, os
import threading
from functools import wraps
import defines
from Crypto.Cipher.AES import block_size as AES_block_size

thread_lock = threading.Lock()
def threadsafe(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with thread_lock:
            return fn(*args, **kwargs)

    return wrapper

class FileObj(BaseFileObj):
    def __init__(self, path, file_attributes = None, creating = False):
        if not file_attributes and creating:
            file_attributes = FILE_ATTRIBUTE.FILE_ATTRIBUTE_NORMAL
        super().__init__(path, file_attributes, creating)
        self.data = None
        #self.data = self.readFile(0, os.path.getsize(self.getNormPath()))
 
    def create(self):
        file = open(self.getNormPath(), "wb+")
        file.close()
        #win32api.SetFileAttributes(self.getNormPath(), self.attributes)

    def open(self):
        if self.data == None:
            self.data = self.readFile(0, self.file_size)

    def close(self):
        self.save()
        self.data = None

    @property
    def file_size(self):
        #return os.stat(self.getNormPath()).st_size
        #return self.len
        #return len(self.data)
        if self.data != None:
            return len(self.data)
        last_block_offset = os.stat(self.getNormPath()).st_size - AES_block_size
        if last_block_offset < 0:
            last_block_offset = 0
        return len(self.readFile(last_block_offset, AES_block_size)) + last_block_offset

    @property
    def allocation_size(self):
        if self.file_size % 4096 == 0:
            return self.file_size
        else:
            return ((self.file_size // 4096) + 1) * 4096

    def read(self, offset, length):
        if not (self.data == None):
            return self.data[offset:offset+length]
        return self.readFile(offset, length) 

    def readFile(self, offset, length):
        #print('[READ FILE]')
        offset_al, length_al = align_offset_length(offset, length)
        
        with open(self.getNormPath(), "rb") as f:
            f.seek(offset_al)
            data = f.read(length_al)

        if (len(data) == 0) :
            return b''
        data_dec = decrypt_file_blocks(offset_al, defines.AES_KEY, data)
        data = data_dec[offset-offset_al:offset-offset_al+length]

        return data
    
    def save(self):
        #print('[SAVE]', self.getNormPath())
        buf_enc = encrypt_file_blocks(0, defines.AES_KEY, self.data)
        
        with open(self.getNormPath(), "wb") as f:
            f.truncate(0)
            f.write(buf_enc)

    @threadsafe
    def write(
        self,
        file_context,
        buffer,
        offset,
        write_to_end_of_file,
        constrained_io
    ):
        #print('[WRITE]')
        length = len(buffer)

        if constrained_io:
            #print("constrained_io")
            if offset >= len(self.data):
                return 0
            end_offset = min(len(self.data), offset + length)
            transferred_length = end_offset - offset
            # self.data[offset:end_offset] = buffer[:transferred_length]
            self.data = self.data[:offset] + buffer[:transferred_length] +  self.data[end_offset:]
            self.save()
            return transferred_length

        else:
            #print("not constrained_io")
            if write_to_end_of_file:
                offset = len(self.data)
            end_offset = offset + length
            self.data = self.data[:offset] + buffer[:end_offset-offset] + self.data[end_offset:]
            #self.data[offset:end_offset] = buffer
            self.save()
            return length