import os
import json

import yaml

from lmdo.oprint import Oprint
from lmdo.chain_processor import ChainProcessor

class FileLoader(ChainProcessor):
    """
    Loading content from yml, json, template files
    and convert them into json object
    """
    def __init__(self, file_path, allowed_ext=None):
        self._file_path = file_path
        self._allowed_ext = allowed_ext

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

            with open(PROJECT_CONFIG_FILE, 'r') as outfile:
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
            return self.loading_strategy()
        except Exception as e:
            Oprint.err(e, 'lmdo')

    @classmethod
    def find_files(cls, path, allowed_file_extensions=None, only_files=None):
        """Find files recursively by giving directory"""
        file_list = []
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if allowed_file_extensions:
                    name, extension = os.path.splitext(filename)
                    if extension in allowed_file_extensions:
                        file_list.append(os.path.join(root, filename))

                if only_files:
                    if filename in only_files:
                        file_list.append(os.path.join(root, filename))

        return file_list
            

