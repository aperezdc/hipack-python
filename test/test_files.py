#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

import unittest2
import hipack
from os import path
from os import listdir


class TestConfigFiles(unittest2.TestCase):
    def check_file(self, filepath):
        f = open(filepath, "rb")
        value = hipack.load(f)
        f.close()
        self.assertTrue(isinstance(value, dict))

    @classmethod
    def setup_tests(cls):
        dirpath = path.abspath(path.dirname(__file__))
        for filename in listdir(dirpath):
            if filename.endswith(".conf"):
                sanitized_name = "test_" + filename[:-5].replace("-", "_")
                filepath = path.join(dirpath, filename)
                setattr(cls, sanitized_name,
                        lambda self: self.check_file(filepath))

    heroes = (
        { u"name": u"Spiderman", u"alter-ego": "Peter Parker" },
        { u"name": u"Superman", u"alter-ego": "Clark Kent" },
        { u"name": u"Batman", u"alter-ego": "Bruce Wayne" },
    )
    def test_framed_input(self):
        with open(path.join(path.dirname(__file__), "heroes.conf"), "rb") as f:
            parser = hipack.Parser(f)
            for hero in self.heroes:
                self.assertEqual(hero, parser.parse_message())

    def test_framed_input_stop_on_eof(self):
        with open(path.join(path.dirname(__file__), "heroes.conf"), "rb") as f:
            parser = hipack.Parser(f)
            i = 0
            while True:
                hero = parser.parse_message()
                if hero is None:
                    break
                self.assertEqual(self.heroes[i], hero)
                i += 1

    def test_framed_input_generator(self):
        with open(path.join(path.dirname(__file__), "heroes.conf"), "rb") as f:
            i = 0
            for hero in hipack.Parser(f).messages():
                self.assertEqual(self.heroes[i], hero)
                i += 1

TestConfigFiles.setup_tests()
