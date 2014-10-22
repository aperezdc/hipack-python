#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import unittest
import wcfg
from os import path
from os import listdir


class TestConfigFiles(unittest.TestCase):
    def check_file(self, filepath):
        f = open(filepath, "rb")
        value = wcfg.load(f)
        f.close()
        self.assertTrue(isinstance(value, dict))


dirpath = path.abspath(path.dirname(__file__))
for filename in listdir(dirpath):
    if not filename.endswith(".conf"):
        continue
    sanitized_name = "test_" + filename[:-5].replace("-", "_")
    filename = path.join(dirpath, filename)
    setattr(TestConfigFiles, sanitized_name,
            lambda self: self.check_file(filename))


