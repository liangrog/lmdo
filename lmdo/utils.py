import os
import errno
import sys
import fnmatch
import zipfile
import re
import site

from lmdo.oprint import Oprint


"""Common utility functions"""


def mkdir(path, mode=0777):
    """Wrapper for mkdir"""
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if e.errno != errno.EEXIST:
            Oprint.err(e, 'lmdo')
            sys.exit(0)
        return True
    return True

def zipper(from_path, target_file_name, exclude=None, delete_exist=True, replace_base_path=None):
    """
    Create zipped package

        exclude = {
            'dir': [],
            'file': []
        }
    """
    # Set compression
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except:
        compression = zipfile.ZIP_STORED

    #delete existing file before writing a new one
    if delete_exist:
        try:
            os.remove(target_file_name)
        except OSError:
            pass
    
    mode = 'a' if not delete_exist else 'w'
    zip_file = zipfile.ZipFile(target_file_name, mode, zipfile.ZIP_DEFLATED)
   
    Oprint.info('Start packaging directory {}'.format(from_path), 'lmdo')
   
    for root, dirs, files in os.walk(from_path):
        bp = root
        if replace_base_path:
            for p_th in replace_base_path:
                if fnmatch.fnmatch(root, '*'+p_th.get('from_path')+'*'):
                    bp = root.replace(p_th.get('from_path'), p_th.get('to_path'))

        if not exclude:
            for f in files:
                zip_file.write(os.path.join(root, f), os.path.join(bp, f))
        else:
            for f in files:
                excl = False
                #check if file/folder should be excluded
                if exclude.get('dir'):
                    for ex_dir in exclude['dir']:
                        if fnmatch.fnmatch(root, ex_dir):
                            excl = True
                            break

                if exclude.get('file'):
                    for ex_file in exclude['file']:
                        if fnmatch.fnmatch(f, ex_file):
                            excl = True
                            break

                if exclude.get('file_with_path'):
                    for ex_file in exclude['file_with_path']:
                        if fnmatch.fnmatch(os.path.join(root, f), ex_file):
                            excl = True
                            break

                if not excl:                    
                    zip_file.write(os.path.join(root, f), os.path.join(bp, f))

    zip_file.close()

    Oprint.info('Finished packaging directory {}. Package {} has been created'.format(from_path, target_file_name), 'lmdo')

    return True

def find_files_by_postfix(path, postfix):
    """Find files with given postfix in path"""
    if type(postfix) == str:
        postfix = [postfix]

    all_files = []
    for root, dirs, files in os.walk(path):
        all_files += files

    return [f for f in all_files if f.split('.').pop() in postfix]

def find_files_by_name_only(path, file_name, allowed_postfix=None):
    """
    Find files in path given file name and filter by postfix if given
    allowed_postfix: []
    """
    all_files = []
    for root, dirs, files in os.walk(path):
        all_files += files

    found_files = [f for f in all_files if fnmatch.fnmatch(f, '{}*'.format(file_name))]
    if allowed_postfix:
        found_files = [f for f in found_files if f.split('.').pop() in allowed_postfix]
        
    return found_files
        
def sys_pause(message, match):
    """pause program to catch user input"""
    name = raw_input(message)
    if not fnmatch.fnmatch(name, match):
        Oprint.err('Exit excecution', 'lmdo')

def update_template(content, to_replace):
    """Replace template content"""
    for k, v in to_replace.iteritems():
        content = content.replace(k, v)
    
    return content

def get_template(name):
    """Find template from package"""
    found_dir = False
    pkg_dir = site.getsitepackages()
    for pd in pkg_dir:
        if os.path.isdir(pd + '/lmdo'):
            found_dir = '{}/lmdo/local_template/{}'.format(pd, name)
            if os.path.isfile(found_dir):
                break
            else:
                found_dir = False
    
    if not found_dir:
        Oprint.warn('Template file {} is missing'.format(name), 'lmdo')

    return found_dir


