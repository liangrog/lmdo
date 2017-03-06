import os
import json

import yaml

from lmdo.oprint import Oprint

class FileLoader(object):
    """
    Loading content from yml, json, template files
    and convert them into json object

    It can only be used at the top of ChainProcessor,
    can not be the successor as it doesn't implement
    the base class ChainProcessor
    """
    def __init__(self, file_path, allowed_ext=None, *args, **kwargs):
        self._file_path = file_path
        self._allowed_ext = allowed_ext
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
        if self._allowed_ext:
            if self.get_ext() not in self._allowed_ext:
                return False
       
        return True

    def is_json(self):
        return True if self.get_ext() == '.json' else False

    def is_template(self):
        return True if self.get_ext() == '.template' else False

    def is_yaml(self):
        return True if self.get_ext() == '.yml' else False

    def loading_strategy(self):
        """Load file into json object"""
        try:
            if not self.file_allowed():
                raise Exception('File type {} is not allowed'.format(self.get_ext()))

            with open(self._file_path, 'r') as outfile:
                content = outfile.read()
                if self.is_json() or self.is_template():
                    return json.loads(content)

                if self.is_yaml():
                    return yaml.load(content)

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
        """Find files recursively by giving directory"""
        file_list = []
        for root, dirnames, filenames in os.walk(search_path):
            for filename in filenames:
                if filename in only_files:
                    file_list.append(os.path.join(root, filename))

        return file_list

