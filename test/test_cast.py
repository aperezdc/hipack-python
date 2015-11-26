#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

from test.util import *
import unittest2
import hipack
import six
from textwrap import dedent


basic_values = (
    (u"0", hipack.ANNOT_INT),
    (u"1.1", hipack.ANNOT_FLOAT),
    (u"True", hipack.ANNOT_BOOL),
    (u"\"\"", hipack.ANNOT_STRING),
    (u"[]", hipack.ANNOT_LIST),
    (u"{}", hipack.ANNOT_DICT),
)
annot_values = (
    (u"0", (".int",)),
    (u":one 0", (".int", "one")),
    (u":one:two 0", (".int", "one", "two")),
    (u":one :two 0", (".int", "one", "two")),
    (u":☺ 0", (".int", u"☺")),       # Unicode
    (u":;%&@ 0", (".int", ";%&@")),  # ASCII symbols
)


class TestCast(unittest2.TestCase):

    @staticmethod
    def parser(string, cast):
        return hipack.Parser(six.BytesIO(string.encode("utf-8")), cast)

    @data(also_annotations(basic_values))
    def test_intrinsic_annots(self, data):
        value, intrinsic_annot = data
        def check_cast(annotations, bytestring, value):
            self.assertIn(intrinsic_annot, annotations)
            return value
        value = self.parser(value, check_cast).parse_value()
        self.assertIsNotNone(value)

    @data(annot_values)
    def test_annots(self, data):
        value, expected = data[0], frozenset(data[1])
        def check_cast(annotations, bytestring, value):
            self.assertEqual(expected, annotations)
            return value
        value = self.parser(value, check_cast).parse_value()
        self.assertIsNotNone(value)

    person_input = dedent("""\
    :person {
        name: "Peter"
        surname: "Parker"
    }
    """)
    def test_create_obj(self):
        class Person(object):
            def __init__(self, name, surname):
                self.name = name
                self.surname = surname
        def obj_cast(annotations, bytestring, value):
            if u"person" in annotations:
                return Person(**value)
            else:
                return value
        value = self.parser(self.person_input, obj_cast).parse_value()
        self.assertIsInstance(value, Person)
        self.assertEqual(value.name, u"Peter")
        self.assertEqual(value.surname, u"Parker")

    http_config = dedent("""\
    myserver::http {
        port 80
        cgi-bin::alias {
            path: "/srv/cgi-scripts/"
        }
        icons::alias {
            path: "/usr/share/icons"
        }
    }
    """)
    def test_create_obj_nested(self):
        class Record(object):
            def __init__(self, **kw):
                self.__dict__.update(kw)
        class HttpServer(Record): pass
        class HttpAlias(Record): pass
        def obj_cast(annotations, bytestring, value):
            if u"alias" in annotations:
                return HttpAlias(**value)
            if u"http" in annotations:
                return HttpServer(**value)
            return value
        value = self.parser(self.http_config, obj_cast).parse_message()
        self.assertIsInstance(value[u"myserver"], HttpServer)
        self.assertIsInstance(value[u"myserver"].icons, HttpAlias)
        self.assertEqual(80, value[u"myserver"].port)

unpack_data(TestCast)
