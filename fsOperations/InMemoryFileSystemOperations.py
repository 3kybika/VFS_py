import argparse
import time
import threading
import os 
from defines import container_path
from functools import wraps
from pathlib import PureWindowsPath

from winfspy import (
    FileSystem, BaseFileSystemOperations, enable_debug_log, FILE_ATTRIBUTE, CREATE_FILE_CREATE_OPTIONS,
    NTStatusObjectNameNotFound, NTStatusDirectoryNotEmpty
)
from winfspy.plumbing.winstuff import filetime_now, SecurityDescriptor

from winfspy.exceptions import NTStatusEndOfFile, NTStatusAccessDenied, NTStatusObjectNameCollision, NTStatusNotADirectory

from filemanager import FileManager

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
    #print(f"{count}:: {msg} {str_kwargs}")


class InMemoryFileSystemOperations(BaseFileSystemOperations, ):
    def __init__(self, volume_label, root_path):
        super().__init__()
        if len(volume_label) > 31:
            raise ValueError("`volume_label` must be 31 characters long max")

        max_file_nodes = 1024
        max_file_size = 4 * 1024 * 1024 * 1024
        file_nodes = 1
        self._volume_info = {
            'total_size': max_file_nodes * max_file_size,
            'free_size': (
                max_file_nodes - file_nodes
            ) * max_file_size,
            'volume_label': volume_label,
        }
        self.root_path = root_path
        self._entries = FileManager(root_path)

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
        logcounted("get_security_by_name", file_name=file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            print(f'=================================== {file_name!r}')
            raise NTStatusObjectNameNotFound()
        #print(file_obj.attributes, file_obj.security_descriptor.handle, file_obj.security_descriptor.size)
        return file_obj.attributes, file_obj.security_descriptor.handle, file_obj.security_descriptor.size

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
        logcounted("create", file_name=file_name)
        # `granted_access` is already handle by winfsp
        # `allocation_size` useless for us
        # `security_descriptor` is not supported yet

        # Retrieve file
        file_name = PureWindowsPath(file_name)
        try:
            parent_file_obj = self._entries[file_name.parent]
            if isinstance(parent_file_obj, FileObj):
                # TODO: check this code is ok
                raise NTStatusNotADirectory()
        except KeyError:
            raise NTStatusObjectNameNotFound()

        # TODO: handle file_attributes

        if create_options & CREATE_FILE_CREATE_OPTIONS.FILE_DIRECTORY_FILE:
            print("creating dir...")
            file_obj = self._entries[file_name] = FolderObj(file_name, self.root_path)
        else:
            print("creating file...")
            file_obj = self._entries[file_name] = FileObj(file_name, self.root_path)

        return OpenedObj(file_obj)

    @threadsafe
    def get_security(
        self, file_context
    ):
        logcounted("get_security", file_context=file_context)
        sd = file_context.file_obj.security_descriptor
        return sd.handle, sd.size

    @threadsafe
    def set_security(
        self, file_context, security_information, modification_descriptor
    ):
        # TODO
        pass

    @threadsafe
    def rename(self, file_context, file_name, new_file_name, replace_if_exists):
        logcounted("rename", file_name = file_name, new_file_name =new_file_name)
        # Retrieve file
        self._entries.renameFile(file_name, new_file_name, replace_if_exists)
        # try:
        #     file_obj = self._entries[file_name]

        # except KeyError:
        #     raise NTStatusObjectNameNotFound()

        # try:
        #     existing_new_file_obj = self._entries[new_file_name]
        #     if not replace_if_exists:
        #         raise NTStatusObjectNameCollision()
        #     if isinstance(file_obj, FileObj):
        #         raise NTStatusAccessDenied()

        # except KeyError:
        #     pass

        # for entry_path, entry in self._entries.items():
        #     try:
        #         relative = entry_path.relative_to(file_name)
        #         new_entry_path = new_file_name / relative
        #         print('===> RENAME', entry_path, new_entry_path)
        #         entry = self._entries.pop(entry_path)
        #         entry.path = new_entry_path
        #         self._entries[new_entry_path] = entry
        #     except ValueError:
        #         continue

    @threadsafe
    def open(
        self, file_name, create_options, granted_access
    ):

        # `granted_access` is already handle by winfsp
        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            print(f'=================================== {file_name!r}')
            raise NTStatusObjectNameNotFound()

        logcounted("open", file_name=file_name)
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
        logcounted("set_file_size", file_context=file_context)

        file_obj = file_context.file_obj
        if not set_allocation_size:
            if new_size < file_obj.file_size:
                file_obj.data = file_obj.data[:new_size]
            elif new_size > file_obj.file_size:
                file_obj.data = file_obj.data + bytearray(new_size - file_obj.file_size)

    def can_delete(self, file_context, file_name: str) -> None:

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound

        if isinstance(file_obj, FolderObj) and not(file_obj.isEmpty()):
            raise NTStatusDirectoryNotEmpty()

    @threadsafe
    def read_directory(
        self, file_context, marker
    ):
        file_obj = file_context.file_obj

        return self._entries.read_directory(file_obj.path)

   
    def read(self, file_context, offset, length):
        logcounted("read", file_context=file_context)
        file_obj = file_context.file_obj

        if offset >= file_obj.file_size:
            raise NTStatusEndOfFile()

        return file_obj.read(offset,offset+length)

    @threadsafe
    def write(
        self,
        file_context,
        buffer,
        offset,
        write_to_end_of_file,
        constrained_io,
    ):
        file_obj = file_context.file_obj
        return file_obj.writing(
            file_context,
            buffer,
            offset,
            write_to_end_of_file,
            constrained_io)

    def cleanup(self, file_context, file_name, flags) -> None:
        # TODO: expose FspCleanupDelete&friends
        if flags & 1:
            try:
                del self._entries[file_name]
            except KeyError:
                raise NTStatusObjectNameNotFound()
