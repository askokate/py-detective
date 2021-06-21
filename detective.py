"""
Implementation of a program to search for occurrences of regular expressions
within a directory tree (a little like 'grep' and a little like 'find').
Output will simply be the relative path to all files in the directory
(or tree) whose name (or content) matches the regex filter.
---------------------------------------------

Usage: python detective.py [options] <path> <regex>

Options:
    -c Look for the regex in file contents; otherwise look at the filename.
    -r Walk the directory structure recursively, examining all sub-folders,
       sub-sub-folder, etc. Otherwise just look in the specified directory.
    -i Perform case-insensitive matching.
    -s Skip hidden files in the tree.
    -S Skip hidden directories in the tree.
    -d List of directories to skip (comma-separated).
    -e List of file extensions to skip (comma-separated).
    -f Follow all symbolic links.
"""
import argparse
import os
import re

import finder
import grepper


def get_regex(args):
    """Get the compiled regex object.

    Args:
        - args: commandline args from user.
    """
    # Combine all of the flags.
    flags = 0
    for flag in args.re_flags:
        flags |= flag
    try:
        r = re.compile(args.regex, flags)
    except re.error:
        raise Exception("Invalid regex.")
    return r


def get_file_finder(args):
    """Get the file finder object.

    Args:
        - args: commandline args from user.
    """
    # Make sure we have empty sets when we have empty strings.
    skip_dirs = set([x for x in args.skip_dirs.split(',') if x])
    skip_exts = set([x for x in args.skip_exts.split(',') if x])
    skip_sub_dirs = not args.recurse_dirs
    ff = finder.Finder(
        skip_sub_dirs=skip_sub_dirs,
        skip_hidden_files=args.skip_hidden_files,
        skip_hidden_dirs=args.skip_hidden_dirs,
        skip_dirs=skip_dirs,
        skip_exts=skip_exts,
        skip_symlink_files=not args.follow_symlinks,
        skip_symlink_dirs=not args.follow_symlinks,
    )
    return ff


def find_files(args):
    """Find the files to grep.

    Args:
        - args: commandline args from user.
    """
    files = []
    if not os.path.exists(args.search_dir):
        raise IOError(2, 'No such path: %r' % args.search_dir)

    ff = get_file_finder(args)
    for filename, k in ff.traverse(args.search_dir):
        if not args.search_contents:
            yield filename, k
        elif k in ('text', 'gzip'):
            yield filename, k


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detect files (names/content) with a given regex pattern.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('-c', '--search-file-contents', action='store_true',
                        default=False, dest='search_contents',
                        help="search file contents too")
    parser.add_argument('-r', '--recurse-dirs', action='store_true',
                        default=False, dest='recurse_dirs',
                        help="walk the directory structure recursively")
    parser.add_argument('-s', '--skip-hidden-files', action='store_true',
                        default=False, help="skip hidden files [default]")
    parser.add_argument('-S', '--skip-hidden-dirs', action='store_true',
                        default=False,
                        help="skip hidden directories [default]")
    parser.add_argument('-d', '--skip-dirs', default='',
                        help="comma-separated list of directory names to skip")
    parser.add_argument('-e', '--skip-exts',
                        default='',
                        help="comma-separated list of file extensions to skip")
    parser.add_argument('-f', '--follow', action='store_true',
                        dest='follow_symlinks',
                        help="follow symlinks to directories and files")
    parser.add_argument('-i', '--ignore-case', action='append_const',
                        dest='re_flags', const=re.I, default=[],
                        help="ignore case in the regex")

    parser.add_argument('search_dir', help="directory to search in")
    parser.add_argument('regex', help="the regular expression to search for")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    g = grepper.Grepper(regex=get_regex(args),
                        search_file_contents=args.search_contents)
    for filename, kind in find_files(args):
        if g.do_grep(filename, kind):
            print(os.path.relpath(filename, args.search_dir))


if __name__ == '__main__':
    main()
