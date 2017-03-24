import yaml
from yaml.representer import SafeRepresenter

# Add block string representer
class folded_str(str): pass

class literal_str(str): pass

class folded_unicode(unicode): pass

class literal_unicode(str): pass

def change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar
    return new_representer


# represent_str does handle some corner cases, so use that
# instead of calling represent_scalar directly
represent_folded_str = change_style('>', SafeRepresenter.represent_str)
represent_literal_str = change_style('|', SafeRepresenter.represent_str)
represent_folded_unicode = change_style('>', SafeRepresenter.represent_unicode)
represent_literal_unicode = change_style('|', SafeRepresenter.represent_unicode)

yaml.add_representer(folded_str, represent_folded_str)
yaml.add_representer(literal_str, represent_literal_str)
yaml.add_representer(folded_unicode, represent_folded_unicode)
yaml.add_representer(literal_unicode, represent_literal_unicode)

