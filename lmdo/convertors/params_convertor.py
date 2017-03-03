
from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor


class ParamsConvertor(Convertor, ChainProcessor):
    """Convert json data to AWS cloudformation parameter list"""
    
    def process(self, data):
        return self.convert(data)

    def convert(self, data):
        # If already is a list, return it
        if type(data) is list:
            return data

        params = []
        for key, value in data:
            params.append(self.get_param_dict(key, value))

        return params

    def get_param_dict(self, key, value):
        return {"ParameterKey": key, "ParameterValue": value}
        

