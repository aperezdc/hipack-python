#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import six
import re


def data(seq):
    def wrapper(f):
        f.test_data_iter = iter(seq)
        return f
    return wrapper

_non_id_chars_re = re.compile(r"[^a-zA-Z0-9_]")
_collapse_underscore_re = re.compile(r"_+")
def _make_id(s):
    if isinstance(s, six.string_types):
        s = str(s.encode("ascii", errors="replace"))
    else:
        s = str(s)
    s = _non_id_chars_re.subn("_", s)[0]
    return _collapse_underscore_re.subn("_", s)[0]

def _make_call_method(func, data_item):
    return lambda self: func(self, data_item)

def unpack_data(cls):
    add_funcs = {}
    del_keys = set()
    for name, value in six.iteritems(cls.__dict__):
        counter = 0
        if name.startswith("test_") and callable(value) \
                and hasattr(value, "test_data_iter"):
            del_keys.add(name)
            for data_item in value.test_data_iter:
                key = name + "_" + str(counter) + "_" + _make_id(data_item)
                add_funcs[key] = _make_call_method(value, data_item)
                counter += 1
    [setattr(cls, name, f) for name, f in six.iteritems(add_funcs)]
    [delattr(cls, name) for name in del_keys]


def also_annotations(sequence):
    for item in iter(sequence):
        yield item
        yield (u":ann1 " + item[0], item[1])
        yield (u":ann1:ann2 " + item[0], item[1])
        yield (u":ann1 :ann2 " + item[0], item[1])
        yield (u":ann1:ann2:ann3 " + item[0], item[1])
        yield (u":ann1 :ann2:ann3 " + item[0], item[1])
        yield (u":ann1:ann2 :ann3 " + item[0], item[1])
        yield (u":ann1 :ann2 :ann3 " + item[0], item[1])
