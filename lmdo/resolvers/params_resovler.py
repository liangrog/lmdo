import os

from lmdo.resolvers import Resolver
from lmdo.convertors import ParamsConvertor, EnvVarConvertor, StackVarConvertor
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

        env_var_convertor.successor = stack_var_convertor
        stack_var_convertor.successor = param_convertor.successor

        for file_path in files:
            file_loader = FileLoader(file_path=file_path, allowed_ext=FILE_LOADER_PARAM_ALLOWED_EXT)
            file_loader.successor = param_convertor
            result += file_loader.process_next()

        return result

    def get_list(self):
        """Get list of params files"""
        if os.path.isfile(self._params_path):
            return [self._params_path]

        if os.path.isdir(self._params_path):
            return FileLoader.find_files(path=self._params_path, allowed_ext=FILE_LOADER_PARAM_ALLOWED_EXT)

        return []


