"""Tests for grepper.py"""
import pytest
import re

import grepper as g


def test_grepper_init():
    test_regex = re.compile("import")
    test_grepper = g.Grepper(test_regex)
    wanted_multiline = re.compile(bytes("import", 'utf-8'),
                                  re.DOTALL | re.MULTILINE)
    assert not test_grepper.search_file_contents
    assert test_grepper.regex_m == wanted_multiline


def test_do_grep_gzip_contents():
    test_regex = re.compile("eggs")
    test_grepper = g.Grepper(test_regex, True)
    assert test_grepper.do_grep("testdata/test.gz", "gzip")


def test_do_grep_text_contents():
    test_regex1 = re.compile("Grepper")
    contents_grepper1 = g.Grepper(test_regex1, True)
    test_regex2 = re.compile("numpy")
    contents_grepper2 = g.Grepper(test_regex2, True)

    assert contents_grepper1.do_grep("grepper.py")
    assert not contents_grepper2.do_grep("grepper.py")


def test_grep_filename():
    test_regex1 = re.compile("import")
    contents_grepper1 = g.Grepper(test_regex1)
    test_regex2 = re.compile("grep")
    contents_grepper2 = g.Grepper(test_regex2)

    assert not contents_grepper1.do_grep("grepper.py")
    assert contents_grepper2.do_grep("grepper.py")
