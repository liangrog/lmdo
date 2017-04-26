import os
import tempfile
import json

import yaml

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
    # Temporary convertion to avoid
    # yaml trying to load function
    # hasn't been defined
    YAML_TO = {'!': '^'}
    TO_YAML = {'^': '!'}

    def __init__(self, template_path, repo_path=None, params_path=None):
        if not os.path.isfile(template_path):
            Oprint.err('Template not found by given path {}'.format(templated_path), 'cloudformation')

        self._template_path = template_path
        self._params_path = params_path
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
        
        def yaml_tmp_ctor(loader, tag_suffix, node):
            if tag.suffix.startswith('!'):
                return node

        _, master_tpl = FileLoader(file_path=self._template_path, allowed_ext=FILE_LOADER_TEMPLATE_ALLOWED_EXT, yaml_replacements=self.YAML_TO).process()
        
        template_urls = []
        for name, resource in master_tpl['Resources'].iteritems():
            if resource['Type'] == 'AWS::CloudFormation::Stack':
                template_urls.append(resource['Properties']['TemplateURL'])
       
        if template_urls:
            for url in template_urls:
                found = NestedTemplateUrlConvertor.match(url)
                if len(found) > 0:
                    for fnd in found:
                      header, template_name = fnd.split("|")
                      templates['children'].append(self.create_template(template_name))
        
        more_childen = self.get_child_template_from_param()
        if more_childen:
            templates['children'] += more_childen

        templates['master'] = self.create_template(self._template_path)
        
        return templates
    
    def get_child_template_from_param(self):
        """Check if we have nested templates from params"""
        if not self._params_path:
            return False

        _, child_tpls = FileLoader(file_path=self._params_path, allowed_ext=FILE_LOADER_TEMPLATE_ALLOWED_EXT).process()
        
        templates = []
        for key, value in child_tpls.iteritems():
            found = NestedTemplateUrlConvertor.match(value)            
            if len(found) > 0:
                for fnd in found:
                  header, template_name = fnd.split("|")
                  templates.append(self.create_template(template_name))

        return templates if len(templates) > 0 else False

    def create_template(self, template_name):
        """Create shadow template for upload"""
        # Setup convertor chain
        env_var_convertor = EnvVarConvertor()
        stack_var_convertor = StackVarConvertor()
        nested_template_convertor = NestedTemplateUrlConvertor()

        env_var_convertor.successor = stack_var_convertor
        stack_var_convertor.successor = nested_template_convertor
         
        if not os.path.isfile(template_name):
            file_path = self.find_template(template_name)
        else: 
            file_path = template_name

        if not file_path:
            Oprint.err('Cannot find template {} in {}'.format(template_name, self._repo_path))

        file_loader = FileLoader(file_path=file_path, allowed_ext=FILE_LOADER_TEMPLATE_ALLOWED_EXT, yaml_replacements=self.YAML_TO)
        file_loader.successor = env_var_convertor
        result, json_content = file_loader.process()
      
        # If it's yaml template, change ^ back to !
        # and dump back with yaml syntax
        if file_loader.isYaml():
            #result = yaml.safe_dump(result, default_flow_style=False, encoding=('utf-8'))
            for key, value in self.TO_YAML.iteritems():
                result = result.replace(key, value)

        template_name = os.path.basename(file_path)
        new_file_path = os.path.join(self._temp_dir, template_name)
        
        with open(new_file_path, 'w+') as f:
            f.write(result)
        f.close()

        return new_file_path

    def find_template(self, template_name):
        """Get list of params files"""
        findings = []
        if os.path.isdir(self._repo_path):
            findings = FileLoader.find_files_by_names(search_path=self._repo_path, only_files=[template_name])
       
        # Only return the first found
        return findings[0] if findings else None


