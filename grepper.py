"""
Class for regex on files.
---------------------------------------------

Module Contents
~~~~~~~~~~~~~~~

The module contains the following public class:

    - :class:`~py-detective.Grepper` -- Container class for searching a pattern
    using regex in a file name or its content.
"""
import gzip
import mmap
import os
import re


class Grepper(object):
    """Container class for object that searchs regex in file name or content.

    Attributes:
        regex : compiled regex object.
        regex_m : multiline enabled regex object.
        search_file_contents : search file contents for regex pattern.
        _openers : dict of file openers.
    """

    def __init__(self, regex, search_file_contents=False):
        self.regex = regex
        # An equivalent regex with multiline enabled.
        self.regex_m = re.compile(bytes(regex.pattern, 'utf-8'),
                                  re.DOTALL | re.MULTILINE)
        self.search_file_contents = search_file_contents
        self._openers = dict(text=open, gzip=gzip.open)

    def _grep_contents(self, fp, kind='text'):
        """Search file contents.

        Args:
            - fp: file object.
        """
        with mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ) as m:
            if kind == 'text':
                if self.regex_m.search(m):
                    return True
            elif kind == 'gzip':
                gzfile = gzip.GzipFile(mode="r", fileobj=m)
                if self.regex_m.search(gzfile.read()):
                    return True
            else:
                raise Exception("Unsupported file type")
        return False

    def do_grep(self, filename, kind='text'):
        """Grep either name of the file or it's content.

        Args:
            - filename: full path to the file.
            - kind: what kind of file - text or gzip.
        """
        if os.stat(filename).st_size != 0:
            if self.search_file_contents:
                # Always open in binary mode
                try:
                    f = self._openers[kind](filename, 'rb')
                    if self._grep_contents(f, kind):
                        return True
                finally:
                    f.close()
            else:
                if self.regex.search(filename):
                    return True
        return False
