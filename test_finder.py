"""Tests for grepper.py"""
import gzip
import os
import pytest
import shutil

import finder


def test_is_binary_file():
    test_file = "testdata/test.gz"
    ff = finder.Finder()
    normal_file = open(test_file, 'rb')
    gzip_file = gzip.open(test_file)
    assert ff._is_binary_file(normal_file)
    assert not ff._is_binary_file(gzip_file)


def test_is_gzipped_text():
    ff = finder.Finder()
    assert ff._is_gzipped_text("testdata/test.gz")
    assert not ff._is_gzipped_text("grepper.py")


def test_categorize_path():
    ff = finder.Finder()
    assert ff.categorize_path("foo") == 'unreadable'


def test_categorize_directory():
    ff1 = finder.Finder()
    ff2 = finder.Finder(skip_hidden_dirs=True)
    os.symlink("testdata", "tt")
    os.mkdir(".hidden-dir")
    assert ff1.categorize_directory(".hidden-dir") == 'directory'
    assert ff2.categorize_directory(".hidden-dir") == 'skip'
    shutil.rmtree(".hidden-dir")
    assert ff1.categorize_directory("tt") == 'link'
    os.unlink("tt")


def test_categorize_file():
    ff1 = finder.Finder()
    assert ff1.categorize_file("testdata/test.gz") == 'gzip'
    assert ff1.categorize_file("grepper.py") == 'text'
    ff2 = finder.Finder(skip_hidden_files=True, skip_symlink_files=True,
                        skip_exts=set('.py'))
    os.symlink("testdata/test.gz", "tt")
    assert ff2.categorize_file('tt') == 'link'
    os.unlink("tt")
    assert ff2.categorize_file('testdata/.file1.txt') == 'skip'
    assert ff2.categorize_file('testdata/sub-dir/file2.bin') == 'binary'
    assert ff2.categorize_file('grepper.py') == 'skip'


def test_traverse():
    ff = finder.Finder(skip_sub_dirs=False)
    files = []
    for fn, k in ff.traverse("testdata/test.gz"):
        files.append((fn, k))
    assert files == [("testdata/test.gz", "gzip"), ]
    files = []
    for fn, k in ff.traverse("testdata"):
        files.append((fn, k))
    assert files == [("testdata/.file1.txt", "text"),
                     ("testdata/sub-dir/file2.bin", "binary"),
                     ("testdata/test.gz", "gzip")]
