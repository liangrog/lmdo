"""
Common utility functions
"""

from __future__ import print_function 

def mkdir(path, mode='0777'):
    """
    Wrapper for mkdir
    """

    import os
    import errno
    import sys

    try:
        os.makedirs(config.tmp_dir, mode)
    except OSError as e:
        if e.errno != errno.EEXIT:
            print(e)
            sys.exit(0)
        return True
    return True

def zipper(self, from_path, target_file_name, exclude=None):
    """
    Create zipped package 
    """

    import zipfile
    import os
    import fnmatch

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
   
    print('Start packaging directory')

    for root, dirs, files in os.walk(from_path):
        if not exclude:
            for file in files:
                f.write(os.path.join(root, file))
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
                        if fnmatch.fnmatch(file, ef):
                            excl = True
                            break

                if not excl:
                    f.write(os.path.join(root, file))

    f.close()

    print('Finished packaging directory' + from_path + '. Zipped package' + target_file_name + ' has been created')

    return True


