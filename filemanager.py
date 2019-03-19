from winfspy.exceptions import NTStatusObjectNameNotFound, NTStatusEndOfFile, NTStatusAccessDenied, NTStatusObjectNameCollision, NTStatusNotADirectory
from objects import *
import os 

class FileManager:  
    def __init__(self, root_path):
        self.root_path = str(root_path)
        
    def getNormPath(self, path):
        return os.path.normpath(self.root_path + '/' + str(path))

    def __getitem__(self, path):
        #ToDo islink() ismount()
        if (os.path.isdir(self.getNormPath(path))):
            return FolderObj(path, self.root_path)
        elif(os.path.isfile(self.getNormPath(path))):
            return FileObj(path, self.root_path)
        raise KeyError()

    def __setitem__(self, key, newFileObject):
        if type(newFileObject) is FileObj:
            file = open(newFileObject.getNormPath(), "wb+")
            file.close()
            #ToDo:attributes
        if type(newFileObject) is FolderObj:
            os.mkdir(newFileObject.getNormPath())
            #ToDo:attributes

    def __delitem__(self, path):
        if (os.path.exists(self.getNormPath(path))):
            os.remove(self.getNormPath(path))
            return
        raise KeyError()

    def read_directory(self, path):
        if (not os.path.isdir(self.getNormPath(path))):
            raise NTStatusObjectNameNotFound()

        entries = []
        # ToDo ?
        #if file_obj.path != PureWindowsPath("/"):
        #    entries.append({'file_name': '..'})

        for file in os.listdir(self.getNormPath(path)) :
            full_path = self.getNormPath(path + '/' + file)
            cur_file_path = os.path.normpath(path + '/' + file)

            if (os.path.isdir(full_path)):
                print("creating dir...", cur_file_path, full_path)
                file_obj = FolderObj(cur_file_path, self.root_path)
            elif (os.path.isfile(full_path)):
                file_obj = FileObj(cur_file_path, self.root_path)
            entries.append({'file_name': file, **file_obj.get_file_info()})
        return entries
    
    def getSize(self, path = "/"):
        total_size = os.path.getsize(self.getNormPath(path))
        for item in os.listdir(self.getNormPath(path)):
            full_path = self.getNormPath(path + '/' + item)
            cur_file_path = os.path.normpath(path + '/' + item)
            if os.path.isfile(full_path):
                total_size += os.path.getsize(full_path)
            elif os.path.isdir(full_path):
                total_size += self.getSize(cur_file_path)
        return total_size

    def renameFile(self, file_name, new_file_name, replace_if_exists):
        if not (os.path.exists(self.getNormPath(file_name))):
            raise NTStatusObjectNameNotFound()

        if (os.path.exists(self.getNormPath(new_file_name))):
            if replace_if_exists:
                os.remove(new_file_name)
            else:
                raise NTStatusObjectNameCollision()
        
        os.rename(self.getNormPath(file_name), self.getNormPath(new_file_name))

    def isdir(self, path = "/"):
        return os.path.isdir(self.getNormPath(path))
    
    def isfile(self, path = "/"):
        return os.path.isfile(self.getNormPath(path))

    
