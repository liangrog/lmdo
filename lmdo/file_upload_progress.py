import os
import sys
import threading


class FileUploadProgress(object):
    """Simple progress tracking for file upload"""

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0.00
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += float(bytes_amount)
            percentage = (self._seen_so_far / self._size) * 100
            
            if percentage >= float(100):
                # Clear stdout

                # Move cursor at the beginning of 
                # the line and clear line
                sys.stdout.write("\033[F\033[K")
                sys.stdout.flush()

                # Move cursor down
                # the line and clear line
                sys.stdout.write("\033[1B\033[K")
                sys.stdout.flush()

                # Move cursor up
                # the line and clear line
                sys.stdout.write("\033[1A\033[K")
                sys.stdout.flush()
            else:
                sys.stdout.write("%s %s %s (%.2f%%) \0\r" % ('Uploading:', self._size, self._seen_so_far, percentage))
                sys.stdout.flush()


