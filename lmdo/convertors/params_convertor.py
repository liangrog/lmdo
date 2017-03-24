
from lmdo.convertors import Convertor
from lmdo.chain_processor import ChainProcessor


class ParamsConvertor(ChainProcessor, Convertor):
    """Convert json data to AWS cloudformation parameter list"""
   
    def process(self, data):
        """Call"""
        return self.convert(data)

    def convert(self, data):
        """Convert data"""
        raw, json_content = data

        # If already is a list, return it
        if type(json_content) is list:
            return raw, json_content

        params = []
        for key, value in json_content.iteritems():
            params.append(self.get_param_dict(key, value))

        return raw, params

    def get_param_dict(self, key, value):
        """AWS param format"""
        return {"ParameterKey": key, "ParameterValue": value}
        

