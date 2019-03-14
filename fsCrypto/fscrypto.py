from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random

AES_KEY = b'very secret12345'


# Выровнять позиции чтения из файла по размеру блока AES
def align_offset_length(offset, length):
    offset_al, length_al = offset, length
    if offset % AES.block_size != 0:
        offset_al -= offset % AES.block_size
        length_al += offset % AES.block_size
    
    if length_al % AES.block_size != 0:
        length_al += AES.block_size - length_al % AES.block_size

    return offset_al, length_al


# Зашифровывает участок файла, data, который начинается с offset
# Участок должен быть выровнен по блокам
def encrypt_file_blocks(offset, key, data):
    if offset % AES.block_size != 0:
        raise Exception('Incorrect offset to encrypt')

    ctr = Counter.new(nbits=128, initial_value=(offset/AES.block_size + 1))

    encryptor = AES.new(key, mode=AES.MODE_CTR, counter=ctr)

    return encryptor.encrypt(data)


# Расшифровывает участок файла, data, который начинается с offset
# Участок должен быть выровнен по блокам
def decrypt_file_blocks(offset, key, data):
    if offset % AES.block_size != 0:
        raise Exception('Incorrect offset to encrypt')

    ctr = Counter.new(nbits=128, initial_value=(offset/AES.block_size + 1))

    decryptor = AES.new(key, mode=AES.MODE_CTR, counter=ctr)

    return decryptor.decrypt(data)
