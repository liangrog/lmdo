import os
import json

from lmdo.lmdo_yaml import yaml
from lmdo.oprint import Oprint

class FileLoader(object):
    """
    Loading content from yml, json, template files
    and convert them into json object

    It can only be used at the top of ChainProcessor,
    can not be the successor as it doesn't implement
    the base class ChainProcessor
    """
    def __init__(self, file_path, allowed_ext=None, yaml_replacements=None):
        self._file_path = file_path
        self._allowed_ext = allowed_ext
        self._yaml_replacements = yaml_replacements
        self._successor = None
    
    @property
    def successor(self):
        return self._successor
    
    @successor.setter
    def successor(self, successor):
        self._successor = successor
   
    def get_ext(self):
        """Get file extension"""
        name, ext = os.path.splitext(self._file_path)
        return ext

    def file_allowed(self):
        """If fiel type is allowed to load"""
        if self._allowed_ext and self.get_ext() not in self._allowed_ext:
            return False
       
        return True

    def isJson(self):
        return True if self.get_ext() == '.json' else False

    def isTemplate(self):
        return True if self.get_ext() == '.template' else False

    def isYaml(self):
        return True if self.get_ext() in ['.yml', '.yaml'] else False

    @staticmethod
    def ifJsonLoadable(data_str):
        """If string is json loadable"""
        try:
            json_obj = json.loads(data_str)
            return json_obj
        except ValueError:
            return False

    @staticmethod
    def ifYamlLoadable(data_str):
        """If string is yaml loadable"""
        try:
            
            json_obj = yaml.load(data_str)
            return json_obj
        except Exception as e:
            return False

    @staticmethod
    def toJson(data_str, file_name=None):
        """Convert string to json"""
        json_str = FileLoader.ifJsonLoadable(data_str)
         
        # Try yaml
        if not json_str:
            json_str = FileLoader.ifYamlLoadable(data_str)
            if not json_str:
                raise ValueError('Data is neither valida json or yaml for file {}'.format(file_name))

        return json_str

    def loading_strategy(self):
        """
        Load file into json object
        Returns a tuple raw and json
        """
        try:
            if not self.file_allowed():
                raise Exception('File type {} is not allowed'.format(self.get_ext()))
            
            with open(self._file_path, 'r') as outfile:
                raw = outfile.read()

                if self.isYaml():
                    if self._yaml_replacements:
                        for key, value in self._yaml_replacements.iteritems():
                            raw = raw.replace(key, value)

                json_content = FileLoader.toJson(raw, file_name=self._file_path)
                    
                return raw, json_content

        except Exception as e:
            Oprint.err(e)
        else:
            raise Exception('File type {} is not allowed'.format(self.get_ext()))

    def process(self):
        """Load file into memory"""
        try:
            if not self._successor:
                return self.loading_strategy()
            else:
                return self._successor.process_next(self.loading_strategy())
        except Exception as e:
            Oprint.err(e, 'lmdo')

    @classmethod
    def find_files_by_extensions(cls, search_path, allowed_ext):
        """Find files recursively by giving directory"""
        file_list = []
        for root, dirnames, filenames in os.walk(search_path):
            for filename in filenames:
                name, extension = os.path.splitext(filename)
                if extension in allowed_ext:
                    file_list.append(os.path.join(root, filename))

        return file_list
            
    @classmethod
    def find_files_by_names(cls, search_path, only_files):
        """
        Find files recursively by giving directory
        files can contain path like 'a/b/c/filename'
        So that we can give file a namespace
        """
        search_list = []
        for filename in only_files:
            tmp_var = filename.split('/')
            file_meta = {
                "file_name": tmp_var.pop(),
                "file_path": '/'.join(tmp_var)
            }

            search_list.append(file_meta)

        file_list = []
        for root, dirnames, filenames in os.walk(search_path):
            for filename in filenames:
                for item in search_list: 
                    if item["file_name"] == filename \
                        and (len(item["file_path"]) == 0 \
                        or (len(item["file_path"]) > 0 and root.endswith(item["file_path"]))):
                        file_list.append(os.path.join(root, filename))

        return file_list

