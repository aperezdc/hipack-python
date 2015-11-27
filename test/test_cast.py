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


if six.PY3:
    def _U(x):
        return str(x, "utf-8")
else:
    def _U(x):
        return unicode(x, "utf-8")

class TestValue(unittest2.TestCase):

    @data((
        ((), "x: 0"),
        (("a",), "x::a 0"),
        (("a", "b"), "x::a:b 0"),
        (("b", "a"), "x::b:a 0"),  # Order matters
    ))
    def test_dump_annot(self, data):
        annotations, expected = data
        text = hipack.dumps({"x": 0}, value=lambda x: (x, annotations))
        self.assertEqual(six.u(expected + "\n"), _U(text))

    @data((
        "col:on", "com,ma",
        "sp ace", "new\nline",
        "carriage\rreturn", "\tab",
        "lbr[acket", "rbr]acket",
        "l{brace", "r}brace",
    ))
    def test_invalid_annots(self, annot):
        with self.assertRaises(ValueError):
            text = hipack.dumps({"x": 0}, value=lambda x: (x, (annot,)))

    def test_serialize_object(self):
        class Person(object):
            def __init__(self, name, surname):
                self.name = name
                self.surname = surname
            def as_dict(self):
                return { "name": self.name, "surname": self.surname }

        def obj_value(obj):
            if isinstance(obj, Person):
                return obj.as_dict(), ("person",)
            return obj, None

        text = hipack.dumps({"spiderman": Person("Peter", "Parker")},
                value=obj_value)
        self.assertEqual(six.u(dedent("""\
                spiderman::person {
                  name: "Peter"
                  surname: "Parker"
                }
                """)), _U(text))

    def test_serialize_object_nested(self):
        class Person(object):
            def __init__(self, name, surname):
                self.name = name
                self.surname = surname
            def as_dict(self):
                return { "name": self.name, "surname": self.surname }
        class Hero(object):
            def __init__(self, nick, alterego):
                self.nick = nick
                self.alterego = alterego
            def as_dict(self):
                return { "nick": self.nick, "alter-ego": self.alterego }

        def obj_value(obj):
            if isinstance(obj, (Person, Hero)):
                return obj.as_dict(), (obj.__class__.__name__,)
            return obj, None

        h = Hero("Spider-Man", Person("Peter", "Parker"))
        expected = dedent("""\
            item::Hero {
              alter-ego::Person {
                name: "Peter"
                surname: "Parker"
              }
              nick: "Spider-Man"
            }
            """)
        text = hipack.dumps({"item": h}, value=obj_value)
        self.assertEqual(six.u(expected), _U(text))

    def test_serialize_duplicate_annotation(self):
        with self.assertRaises(ValueError):
            hipack.dumps({"x":0}, value=lambda x: (x, ("a", "a")))

unpack_data(TestValue)
