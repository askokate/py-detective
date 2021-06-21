"""
Class for finding files.
---------------------------------------------

Module Contents
~~~~~~~~~~~~~~~

The module contains the following public class:

    - :class:`~py-detective.Finder` -- Container class for finding files
    in a path recursively, that satisfy certain conditions.
"""
import gzip
import os
import stat
import sys


def f(ints):
    return ''.join(map(chr, ints))


if sys.version_info[0] > 2:
    ints2bytes = bytes
else:
    ints2bytes = f

TEXTCHARS = ints2bytes([7, 8, 9, 10, 12, 13, 27] + list(range(0x20, 0x100)))
ALLBYTES = ints2bytes(range(256))

# magic header bytes for gzip.
GZIP_MAGIC = b'\037\213'


class Finder(object):
    """Container class for object that finds searchable files.

    Attributes:
        skip_sub_dirs : skip sub directories.
        skip_hidden_dirs : skip hidden directories.
        skip_hidden_files : skip hidden files.
        skip_dirs : list of directory names to skip.
        skip_exts : list of file extensions to skip while searching file
                    contents. ex: png, jpeg.
        skip_symlink_dirs : skip symlinked directories.
        skip_symlink_files : skip symlinked files.
        binary_bytes : number of bytes to check at the beginning and end of a
                       file for binary characters.
    """

    def __init__(self, skip_sub_dirs=True, skip_hidden_dirs=False,
                 skip_hidden_files=False, skip_dirs=set(), skip_exts=set(),
                 skip_symlink_dirs=True, skip_symlink_files=True,
                 binary_bytes=4096):
        self.skip_sub_dirs = skip_sub_dirs
        self.skip_hidden_dirs = skip_hidden_dirs
        self.skip_hidden_files = skip_hidden_files
        self.skip_dirs = skip_dirs
        self.skip_symlink_dirs = skip_symlink_dirs
        self.skip_symlink_files = skip_symlink_files
        self.binary_bytes = binary_bytes

        self.skip_exts_simple = set()
        self.skip_exts_endswith = list()
        for ext in skip_exts:
            if os.path.splitext('foo.bar'+ext)[1] == ext:
                self.skip_exts_simple.add(ext)
            else:
                self.skip_exts_endswith.append(ext)

    def _is_binary_file(self, f):
        """Check if the file is in binary format

        Args:
            - f: file object for reading
        """
        is_binary = False
        try:
            bytes = f.read(self.binary_bytes)
        except Exception as e:
            # assume binary, in case of an error.
            is_binary = True
        nontext = bytes.translate(ALLBYTES, TEXTCHARS)
        is_binary = bool(nontext)
        f.close()
        return is_binary

    def _is_gzipped_text(self, filename):
        """Check if the file is in gzipped text file format

        Args:
            - filename: full path to the file to check
        """
        is_gzipped_text = False
        f = open(filename, 'rb')
        marker = f.read(2)
        f.close()
        if marker == GZIP_MAGIC:
            f = gzip.open(filename)
            try:
                is_gzipped_text = not self._is_binary_file(f)
            except IOError:
                is_gzipped_text = False
        return is_gzipped_text

    def categorize_path(self, path_str):
        """Determine what kind of path string is.

        Args:
            - path_str: path string
        """
        try:
            st_mode = os.stat(path_str).st_mode
            if stat.S_ISREG(st_mode):
                return self.categorize_file(path_str)
            elif stat.S_ISDIR(st_mode):
                return self.categorize_directory(path_str)
            else:
                return 'skip'
        except OSError:
            return 'unreadable'

    def categorize_directory(self, dir_path):
        """Categorize directory path as 'skip', 'link' or 'directory'.

        Args:
            - dir_path: full path to the directory to categorize
        """
        basename = os.path.split(dir_path)[-1]
        if (self.skip_hidden_dirs and
                basename.startswith('.') and
                basename not in ('.', '..')):
            return 'skip'
        if self.skip_symlink_dirs and os.path.islink(dir_path):
            return 'link'
        if basename in self.skip_dirs:
            return 'skip'
        return 'directory'

    def categorize_file(self, file_path):
        """Categorize file path as 'skip', 'link', 'gzip', 'binary', 'text' or
        'unreadable'.

        Args:
            - file_path: full path to the file to categorize
        """
        basename = os.path.split(file_path)[-1]
        if self.skip_hidden_files and basename.startswith('.'):
            return 'skip'
        if self.skip_symlink_files and os.path.islink(file_path):
            return 'link'
        file_path_nc = os.path.normcase(file_path)
        ext = os.path.splitext(file_path_nc)[1]
        if ext in self.skip_exts_simple or ext.startswith('.~'):
            return 'skip'
        for ext in self.skip_exts_endswith:
            if file_path_nc.endswith(ext):
                return 'skip'
        try:
            f = open(file_path, 'rb')
            if self._is_binary_file(f):
                if self._is_gzipped_text(file_path):
                    return 'gzip'
                else:
                    return 'binary'
            else:
                return 'text'
        except (OSError, IOError):
            return 'unreadable'

    def traverse(self, startpath):
        """Traverse the directory tree from a given start path yielding all
        of the files and their kinds underneath it depth first. Paths which are
        categorized as 'skip', 'link', or 'unreadable' will simply be passed
        over without comment.

        Args:
            - startpath: path to start the directory tree traversal
        """
        kind = self.categorize_path(startpath)
        if kind in ('binary', 'text', 'gzip'):
            yield startpath, kind
        elif kind == 'directory':
            try:
                basenames = os.listdir(startpath)
            except OSError:
                return
            for basename in sorted(basenames):
                path = os.path.join(startpath, basename)
                kind = self.categorize_path(path)
                if kind in ('binary', 'text', 'gzip'):
                    yield path, kind
                elif kind == 'directory':
                    if not self.skip_sub_dirs:
                        for fn, k in self.traverse(path):
                            yield fn, k
