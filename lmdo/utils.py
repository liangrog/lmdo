import os
import errno
import sys
import fnmatch
import zipfile

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

def zipper(from_path, target_file_name, exclude=None):
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
    try:
        os.remove(target_file_name)
    except OSError:
        pass

    zip_file = zipfile.ZipFile(target_file_name, 'w', zipfile.ZIP_DEFLATED)
   
    Oprint.info('Start packaging directory {}'.format(from_path), 'lmdo')
   
    for root, dirs, files in os.walk(from_path):
        if not exclude:
            for file in files:
                zip_file.write(os.path.join(root, file))
        else:
            for file in files:
                excl = False

                #check if file/folder should be excluded
                if exclude['dir']:
                    for ex_dir in exclude['dir']:
                        if fnmatch.fnmatch(root, ex_dir):
                            excl = True
                            break

                if exclude['file']:
                    for ex_file in exclude['file']:
                        if fnmatch.fnmatch(file, ex_file):
                            excl = True
                            break

                if not excl:
                    zip_file.write(os.path.join(root, file))

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

 
