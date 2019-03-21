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

from objects import *

thread_lock = threading.Lock()

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
        max_file_size = 16 * 1024 * 1024 * 1024 * 1024
        file_nodes = 1
        self._volume_info = {
            'total_size': max_file_nodes * max_file_size,
            'free_size': (
                max_file_nodes - file_nodes
            ) * max_file_size,
            'volume_label': volume_label,
        }

        #root_path = #PureWindowsPath("/")
        self._entries = self.buildFileTree(root_path)
        print("Starting...")


    def buildFileTree(self, root="./"):
        files = []

        files.append({"filename":"", "path":""})
        entries = {}

        for file in files:            
            full_path = os.path.normpath(file["path"] +"/"+ file["filename"])
            real_path = root + full_path 
            print(full_path)
            if os.path.isdir(real_path):
                for file in os.listdir(root + full_path):
                    files.append({"filename": file, "path": full_path})
                entries[PureWindowsPath(full_path)] = FolderObj(str(full_path))
            elif os.path.isfile(real_path):
                offset = 0
                length = os.stat(real_path).st_size

                entries[PureWindowsPath(full_path)] = FileObj(str(full_path))

        return entries 

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
        file_name = PureWindowsPath(file_name)
        logcounted("get_security_by_name", file_name=file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            print(f'=================================== {file_name!r}')
            raise NTStatusObjectNameNotFound()

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
        file_name = PureWindowsPath(file_name)
        # `granted_access` is already handle by winfsp
        # `allocation_size` useless for us
        # `security_descriptor` is not supported yet

        # Retrieve file
        try:
            parent_file_obj = self._entries[file_name.parent]
            if isinstance(parent_file_obj, FileObj):
                # TODO: check this code is ok
                raise NTStatusNotADirectory()
        except KeyError:
            raise NTStatusObjectNameNotFound()

        # TODO: handle file_attributes

        if create_options & CREATE_FILE_CREATE_OPTIONS.FILE_DIRECTORY_FILE:
            file_obj = self._entries[file_name] = FolderObj(file_name, file_attributes, True)
        else:
            file_obj = self._entries[file_name] = FileObj(file_name, file_attributes, True)
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
        print("renaming")
        file_name = PureWindowsPath(file_name)
        new_file_name = PureWindowsPath(new_file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]

        except KeyError:
            raise NTStatusObjectNameNotFound()

        try:
            existing_new_file_obj = self._entries[new_file_name]
            if not replace_if_exists:
                raise NTStatusObjectNameCollision()
            if isinstance(file_obj, FileObj):
                raise NTStatusAccessDenied()
            
        except KeyError:
            pass
        file_obj.rename(new_file_name)
        for entry_path, entry in self._entries.items():
            try:
                relative = entry_path.relative_to(file_name)
                new_entry_path = new_file_name / relative
                print('===> RENAME', entry_path, new_entry_path)
                entry = self._entries.pop(entry_path)
                entry.path = new_entry_path
                self._entries[new_entry_path] = entry
            except ValueError:
                continue

    @threadsafe
    def open(
        self, file_name, create_options, granted_access
    ):
        file_name = PureWindowsPath(file_name)

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
        print("file_attributes", file_attributes)
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
        file_name = PureWindowsPath(file_name)

        # Retrieve file
        try:
            file_obj = self._entries[file_name]
        except KeyError:
            raise NTStatusObjectNameNotFound

        if isinstance(file_obj, FolderObj):
            for entry in self._entries.keys():
                try:
                    if entry.relative_to(file_name).parts:
                        raise NTStatusDirectoryNotEmpty()
                except ValueError:
                    continue

    @threadsafe
    def read_directory(
        self, file_context, marker
    ):
        entries = []
        file_obj = file_context.file_obj

        if file_obj.path != PureWindowsPath("/"):
            entries.append({'file_name': '..'})

        for entry_path, entry_obj in self._entries.items():
            try:
                relative = entry_path.relative_to(file_obj.path)
                # Not interested into ourself or our grandchildren
                if len(relative.parts) == 1:
                    print('==> ADD', entry_path)
                    entries.append({'file_name': entry_path.name, **entry_obj.get_file_info()})
            except ValueError:
                continue
        return entries

    @threadsafe
    def read(self, file_context, offset, length):
        logcounted("read", file_context=file_context)
        file_obj = file_context.file_obj

        if offset >= file_obj.file_size:
            raise NTStatusEndOfFile()
        #return file_obj.read(offset, length)
        return file_obj.data[offset:offset+length]

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
        #print("WRITING...")
        return file_obj.write(
            file_context,
            buffer,
            offset,
            write_to_end_of_file,
            constrained_io
        )
     
        # length = len(buffer)

        # if constrained_io:
        #    if offset >= len(file_obj.data):
        #        return 0
        #    end_offset = min(len(file_obj.data), offset + length)
        #    transferred_length = end_offset - offset
        #    # file_obj.data[offset:end_offset] = buffer[:transferred_length]
        #    file_obj.data = file_obj.data[:offset] + buffer[:transferred_length] +  file_obj.data[end_offset:]
        #    file_obj.save()
        #    return transferred_length

        # else:
        #    if write_to_end_of_file:
        #        offset = len(file_obj.data)
        #    end_offset = offset + length
        #    file_obj.data = file_obj.data[:offset] + buffer + file_obj.data[end_offset:]
        #    #file_obj.data[offset:end_offset] = buffer
        #    file_obj.save()
        #    return length

    @threadsafe
    def cleanup(self, file_context, file_name, flags) -> None:
        # TODO: expose FspCleanupDelete&friends
        if flags & 1:
            file_name = PureWindowsPath(file_name)
            try:
                self._entries[file_name].remove()
                del self._entries[file_name]
            except KeyError:
                raise NTStatusObjectNameNotFound()
    
    def overwrite(self, file_context, file_attributes, replace_file_attributes, allocation_size) -> None:
        pass
    
    def flush(self, file_context):
        file_context.file_obj.save()
        pass