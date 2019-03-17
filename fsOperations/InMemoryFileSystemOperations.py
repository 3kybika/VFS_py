import argparse
import time
import threading
import os 
from defines import container_path
from functools import wraps
from pathlib import PureWindowsPath

from winfspy import (
    FileSystem, BaseFileSystemOperations, enable_debug_log, FILE_ATTRIBUTE, CREATE_FILE_CREATE_OPTIONS,
    NTStatusObjectNameNotFound, NTStatusDirectoryNotEmpty, exceptions
)

from winfspy.exceptions import NTStatusEndOfFile, NTStatusAccessDenied, NTStatusObjectNameCollision, NTStatusNotADirectory

from winfspy.plumbing.winstuff import filetime_now, security_descriptor_factory
thread_lock = threading.Lock()

from objects import *

def threadsafe(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with thread_lock:
            return fn(*args, **kwargs)

    return wrapper

count = 0
def logcounted(msg, **kwargs):
    global count
    count += 1
    str_kwargs = ', '.join(f"{k}={v!r}" for k, v in kwargs.items())
    print(f"{count}:: {msg} {str_kwargs}")

class InMemoryFileSystemOperations(BaseFileSystemOperations):
    def __init__(self, volume_label, root_path = "./"):
        super().__init__()
        if len(volume_label) > 31:
            raise ValueError("`volume_label` must be 31 characters long max")

        max_file_nodes = 1024
        max_file_size = 7 * 1024 * 1024
        file_nodes = 1
        self._volume_info = {
            'total_size': max_file_nodes * max_file_size,
            'free_size': (
                max_file_nodes - file_nodes
            ) * max_file_size,
            'volume_label': volume_label,
        }

    @staticmethod
    def normalizePath(path):
        print("unNormalize path = ", path)
        path = os.path.normpath(container_path + '/' + path)
        return path

    @threadsafe
    def get_volume_info(self):
        return self._volume_info

    @threadsafe
    def set_volume_label(self, volume_label):
        self._volume_info['volume_label'] = volume_label

    @threadsafe
    def get_security_by_name(
        self,
        file_name,
    ):
        norm_path = self.normalizePath(file_name)
        logcounted("get_security_by_name", file_name=file_name)
        
        # Retrieve file
        file_obj = None
        try:
            if (os.path.isdir(norm_path) or file_name == '\\'):
                file_obj = FolderObj(file_name, False)
            elif (os.path.isfile(norm_path)):
                file_obj = FileObj(file_name, False)
            else:
                raise NTStatusObjectNameNotFound()
        except KeyError:
            print(f'=================================== {file_name!r}')
            raise NTStatusObjectNameNotFound()

        return {
            'file_attributes': file_obj.attributes,
            'security_descriptor': None  # TODO
        }

    @threadsafe
    def create(
        self,
        file_name,
        create_options,
        granted_access,
        file_attributes,
        security_descriptor,
        allocation_size
    ):
        
        file_name = PureWindowsPath(file_name)
        logcounted("create", file_name=file_name)
        # `granted_access` is already handle by winfsp
        # `allocation_size` useless for us
        # `security_descriptor` is not supported yet

        # Retrieve file
        if (os.path.isfile(container_path + str(file_name.parent))):
            raise NTStatusNotADirectory()
        if (not os.path.isdir(container_path + str(file_name.parent))): 
            raise NTStatusObjectNameNotFound()

        # TODO: handle file_attributes
        if (create_options & CREATE_FILE_CREATE_OPTIONS.FILE_DIRECTORY_FILE):
            # TODO: check attributes 
            file_obj = FolderObj(file_name, True)
        else:
            file_obj = FileObj(file_name, True, file_attributes)

        return OpenedObj(file_obj)

    @threadsafe
    def get_security(
        self, file_context
    ):
        logcounted("get_security", file_context=file_context)

    @threadsafe
    def set_security(
        self, file_context, security_information, modification_descriptor
    ):
        # TODO
        pass

    @threadsafe
    def rename(self, file_context, file_name, new_file_name, replace_if_exists):
        logcounted("rename", file_context=file_context)

        file_name = PureWindowsPath(file_name)
        new_file_name = PureWindowsPath(new_file_name)

        # Retrieve file
        if (not os.path.exists(container_path + str(file_name))):
            raise NTStatusObjectNameNotFound()
       
        if (os.path.exists(container_path + str(new_file_name))):
            if not replace_if_exists:
                raise NTStatusObjectNameCollision()
            os.remove(container_path + str(new_file_name))

        try:
            os.rename(
                container_path + str(new_file_name), 
                container_path + str(new_file_name)
            )
        except Exception:
            raise NTStatusAccessDenied()

    @threadsafe
    def open(
        self, file_name, create_options, granted_access
    ):
        #file_name = PureWindowsPath(file_name)

        # `granted_access` is already handle by winfsp

        # Retrieve file
        logcounted("open", file_name=file_name)

        full_path = self.normalizePath(file_name)
        
        full_path = './' + os.path.normpath(container_path + file_name)
        print(full_path)

        try:
            if (os.path.isfile(full_path)):
                file_obj = FileObj(file_name, False)
                print("Opened file...")
            elif(os.path.isdir(full_path) or file_name == '\\'):
                file_obj = FolderObj(file_name, False)
                print("Opened dir...")    
            else:    
                raise NTStatusObjectNameNotFound()
        except KeyError:
            print(f'=================================== {file_name!r}')
            raise NTStatusObjectNameNotFound()
        except Exception as e:
            print(e)
            print(f'Can\'t open by unknown reason {full_path}')
            raise e
        
        return OpenedObj(file_obj)

    @threadsafe
    def close(self, file_context):
        logcounted("close", file_context=file_context)

    @threadsafe
    def get_file_info(self, file_context):
        logcounted("get_file_info", file_context=file_context)
        return file_context.file_obj.get_file_info()

    @threadsafe
    def set_basic_info(self, file_context, file_attributes, creation_time, last_access_time, last_write_time, change_time, file_info) -> dict:
        logcounted("set_basic_info", file_context=file_context)

        file_obj = file_context.file_obj
        if file_attributes != FILE_ATTRIBUTE.INVALID_FILE_ATTRIBUTES:
            file_obj.file_attributes = file_attributes
        if creation_time:
            file_obj.creation_time = creation_time
        if last_access_time:
            file_obj.last_access_time = last_access_time
        if last_write_time:
            file_obj.last_write_time = last_write_time
        if change_time:
            file_obj.change_time = change_time

        return file_obj.get_file_info()

    @threadsafe
    def set_file_size(self, file_context, new_size, set_allocation_size):
        #ToDo
        logcounted("set_file_size", file_context=file_context)

        file_obj = file_context.file_obj
        return
        if not set_allocation_size:
            if new_size < file_obj.file_size:
                file_obj.data = file_obj.data[:new_size]
            elif new_size > file_obj.file_size:
                file_obj.data = file_obj.data + bytearray(new_size - file_obj.file_size)

    def can_delete(self, file_context, file_name: str) -> None:
        #file_name = PureWindowsPath(file_name)
        logcounted("can_delete", file_name=file_name)
        # Retrieve file
        if (os.path.isdir(container_path + file_name)):
            if len(os.listdir(container_path + file_name)):
                raise NTStatusDirectoryNotEmpty()
        
        if (not os.path.isfile(container_path + file_name)):
            raise NTStatusObjectNameNotFound()
       
    @threadsafe
    def read_directory(
        self, file_context, marker
    ):
        logcounted("read_directory", file_name=file_context.file_obj.path)
        file_name = file_context.file_obj.path
        if (not os.path.isdir(self.normalizePath(file_name))):
            raise NTStatusObjectNameNotFound()
        
        entries = []
        for file in os.listdir(container_path + file_context.file_obj.path) :
            full_path = self.normalizePath(file_name + '/' + file)
            cur_file_path = os.path.normpath(file_name + '/' + file)

            if (os.path.isdir(full_path) or cur_file_path == '\\'):
                print("creating dir...", cur_file_path, full_path)
                file_obj = FolderObj(cur_file_path, False)
            elif (os.path.isfile(full_path)):
                file_obj = FileObj(cur_file_path, False)
            entries.append({'file_name': file, **file_obj.get_file_info()})
        
        return entries

    @threadsafe
    def read(self, file_context, offset, length):
        logcounted("read", file_context=file_context)
        file_obj = file_context.file_obj
        if offset >= file_obj.file_size:  
            raise NTStatusEndOfFile()

        return file_obj.read(offset, length)

    @threadsafe
    def write(
        self,
        file_context,
        buffer,
        offset,
        write_to_end_of_file,
        constrained_io,
    ):
        logcounted("write", file_name=file_context.file_obj.path)
        print("write_to_end_of_file", write_to_end_of_file, "constrained_io", constrained_io )
        file_obj = file_context.file_obj
        length = len(buffer)
        
        buffer = b''.join([i for i in buffer])

        file_obj.write(offset, length, buffer, write_to_end_of_file)
        return length
        # if constrained_io:x
        #     if offset >= file_obj.file_size():
        #         return 0
        #     end_offset = min(file_obj.file_size(), offset + length)
        #     transferred_length = end_offset - offset
        #     file_obj.write(offset, length, buffer[:transferred_length])
        #     return transferred_length
        # else:
            
        # else:
        #     print("[INFO] writing in end of file")
        #     if write_to_end_of_file:
        #         offset = file_obj.file_size()
        #     end_offset = offset + length
        #     file_obj.write(offset, length, buffer)
        #     return length

    def cleanup(self, file_context, file_name, flags) -> None:
        # TODO: expose FspCleanupDelete&friends
        print("[INFO] cleanup file")
        if flags & 1:
            try:
                os.remove(self.normalizePath(file_name))
            except KeyError:
                raise NTStatusObjectNameNotFound()
