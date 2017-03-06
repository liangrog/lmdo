import os
import tempfile
import json

from lmdo.resolvers import Resolver
from lmdo.convertors.env_var_convertor import EnvVarConvertor
from lmdo.convertors.stack_var_convertor import StackVarConvertor
from lmdo.convertors.nested_template_url_convertor import NestedTemplateUrlConvertor
from lmdo.file_loader import FileLoader
from lmdo.config import FILE_LOADER_TEMPLATE_ALLOWED_EXT 
from lmdo.oprint import Oprint


class TemplatesResolver(Resolver):
    """
    Resolve templates
    """
    def __init__(self, template_path, repo_path=None):
        if not os.path.isfile(template_path):
            Oprint.err('Template not found by given path {}'.format(templated_path), 'cloudformation')

        self._template_path = template_path
        # Default to project root if not given
        self._repo_path = repo_path or './'
        self._temp_dir = tempfile.mkdtemp()

    def resolve(self):
        return self.get_templates()

    def get_templates(self):
        """Get all the nested stacks"""
        # Create master template
        templates = {
            "tmp_dir": self._temp_dir,
            "master": None,
            "children": []
        }

        templates['master'] = self._template_path
        with open(templates['master'], 'r') as outfile:
            master_tpl = json.loads(outfile.read())

        template_urls = []
        for name, resource in master_tpl['Resources'].iteritems():
            if resource['Type'] == 'AWS::CloudFormation::Stack':
                template_urls.append(resource['Properties']['TemplateURL'])
        
        if template_urls:
            for url in template_urls:
                if url.startswith('$template'):
                    header, template_name = url.split("|")
                    templates['children'].append(self.create_template(template_name))

        return templates

    def create_template(self, template_name):
        """Create shadow template for upload"""
        # Setup convertor chain
        env_var_convertor = EnvVarConvertor()
        stack_var_convertor = StackVarConvertor()
        nested_template_convertor = NestedTemplateUrlConvertor()

        env_var_convertor.successor = stack_var_convertor
        stack_var_convertor.successor = nested_template_convertor

        file_path = self.find_template(template_name)
        if not file_path:
            Oprint.err('Cannot find template {} in {}'.format(template_name, self._repo_path))

        file_loader = FileLoader(file_path=file_path, allowed_ext=FILE_LOADER_TEMPLATE_ALLOWED_EXT)
        file_loader.successor = env_var_convertor
        result = file_loader.process()

        template_name = os.path.basename(file_path)
        new_file_path = os.path.join(self._temp_dir, template_name)
        with open(new_file_path, 'w+') as f:
            f.write(unicode(result))
        f.close()

        return new_file_path

    def find_template(self, template_name):
        """Get list of params files"""
        findings = []
        if os.path.isdir(self._repo_path):
            findings = FileLoader.find_files_by_names(search_path=self._repo_path, only_files=[template_name])
       
        print(findings)
        # Only return the first found
        return findings[0] if findings else None


