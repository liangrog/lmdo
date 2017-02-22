import os
import errno
import sys
import fnmatch
import zipfile
import re
import site
import time
import shutil
from functools import wraps

from botocore.exceptions import ClientError

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
 
def copytree(src, dst, symlinks=False, ignore=None):
    """Copy content to new destination"""
    names = os.listdir(src)

    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    errors = []
    for name in names:
        if name.endswith('.pyc'):
            continue

        if name in ignored_names:
            continue
        
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)

        # Delete if exists
        if os.path.exists(dstname):
            try:
                shutil.rmtree(dstname)
            except Exception as e:
                os.unlink(dstname)

        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                shutil.copytree(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Exception as err:
            errors.extend(str(err))
    try:
        shutil.copystat(src, dst)
    #except WindowsError:
        # can't copy file access times on Windows
    #    pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise Exception(errors)
       
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
    pkg_dir = get_sitepackage_dirs()
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

def get_sitepackage_dirs():
    """Find site packages, work with virtualenv 2.7"""
    if 'getsitepackages' in dir(site):
        return site.getsitepackages()
    else:
        # workaround for https://github.com/pypa/virtualenv/issues/355
        return sys.path

def class_function_retry(aws_retry_condition=False, tries=3, delay=1, backoff=2):
    def retry(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            c_tries = tries
            c_delay = delay
            c_backoff = backoff
            while c_tries > 1:
                try:
                    return func(self, *args, **kwargs)
                except ClientError as ce:
                    Oprint.warn(str(ce.response['Error']['Message']), 'aws')
                    if aws_retry_condition:
                        code = ce.response['Error']['Code']
                        # If it's not in the retry condition set tries to 1 so to stop the while loop
                        if (type(aws_retry_condition) is str and aws_retry_condition != code) or \
                            (type(aws_retry_condition) is list and code not in aws_retry_condition):
                                c_tries = 1
                except Exception as e:
                    Oprint.warn(e, 'lmdo')

                c_tries -= 1
                if c_tries > 1:
                    Oprint.warn('Retrying in {} seconds'.format(c_delay), 'lmdo')
                    time.sleep(c_delay)
                    
                c_delay *= c_backoff

        return wrapper
    return retry

 
