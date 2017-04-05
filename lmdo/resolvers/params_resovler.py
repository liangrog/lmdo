import os

from lmdo.resolvers import Resolver
from lmdo.convertors.env_var_convertor import EnvVarConvertor
from lmdo.convertors.stack_var_convertor import StackVarConvertor
from lmdo.convertors.params_convertor import ParamsConvertor
from lmdo.convertors.nested_template_url_convertor import NestedTemplateUrlConvertor
from lmdo.file_loader import FileLoader
from lmdo.config import FILE_LOADER_PARAM_ALLOWED_EXT 


class ParamsResolver(Resolver):
    """
    Resolve stack parameters
    1. If param folder provided, merge all files
    2. If a param file provided, use it
    """
    def __init__(self, params_path):
        self._params_path = params_path

    def resolve(self):
        return self.merge()

    def merge(self):
        """Merge all param files into one"""
        files = self.get_list()
        result = []

        # Setup convertor chain
        param_convertor = ParamsConvertor()
        env_var_convertor = EnvVarConvertor()
        stack_var_convertor = StackVarConvertor()
        nested_template_convertor = NestedTemplateUrlConvertor()

        env_var_convertor.successor = stack_var_convertor
        stack_var_convertor.successor = nested_template_convertor
        nested_template_convertor.successor = param_convertor

        for file_path in files:
            file_loader = FileLoader(file_path=file_path, allowed_ext=FILE_LOADER_PARAM_ALLOWED_EXT)
            file_loader.successor = env_var_convertor
            raw, json_content = file_loader.process()
            result += json_content
        
        return result

    def get_list(self):
        """Get list of params files"""
        if os.path.isfile(self._params_path):
            return [self._params_path]

        if os.path.isdir(self._params_path):
            return FileLoader.find_files_by_extensions(search_path=self._params_path, allowed_ext=FILE_LOADER_PARAM_ALLOWED_EXT)

        return []


