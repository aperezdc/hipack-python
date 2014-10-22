#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

import unittest
import wcfg
import six
from textwrap import dedent


class TestParser(unittest.TestCase):

    @staticmethod
    def parser(string):
        return wcfg.Parser(six.BytesIO(string.encode("utf-8")))

    def test_parse_valid_booleans(self):
        booleans = (
            (u"True", True),
            (u"true", True),
            (u"False", False),
            (u"false", False),
        )
        for item, expected in booleans:
            value = self.parser(item).parse_bool()
            self.assertEquals(expected, value)
            self.assertTrue(isinstance(value, bool))

    def check_numbers(self, numbers, type_):
        for item, result in numbers:
            value = self.parser(item).parse_number()
            self.assertEquals(result, value)
            self.assertTrue(isinstance(value, type_))
            # Trailing whitespace must not alter the result.
            value = self.parser(item + " ").parse_number()
            self.assertEquals(result, value)
            self.assertTrue(isinstance(value, type_))

    def test_parse_valid_integer_numbers(self):
        numbers = (
            (u"1", 1),
            (u"+1", 1),
            (u"-2", -2),
            (u"123", 123),
            (u"+123", 123),
            (u"-123", -123),
        )
        self.check_numbers(numbers, six.integer_types)

    def test_parse_valid_hex_numbers(self):
        numbers = (
            (u"0x1", 1),
            (u"0X1", 1),
            (u"0xcafe", 0xCAFE),
            (u"0XCAFE", 0xCAFE),
            (u"0xCAFE", 0xCAFE),
            (u"0xCaFe", 0xCAFE),
            (u"0x1234", 0x1234),
            (u"0xC00FFEE", 0xC00FFEE),
            (u"0xdeadbeef", 0xdeadbeef),
        )
        self.check_numbers(numbers, six.integer_types)

    def test_parse_valid_octal_numbers(self):
        numbers = (
            (u"01", 0o1),
            (u"01234567", 0o1234567),
            (u"042", 0o42),
        )
        self.check_numbers(numbers, six.integer_types)

    def test_parse_valid_float_numbers(self):
        numbers = (
            (u"1.", 1.0),
            (u".5", 0.5),
            (u"1.5", 1.5),
            (u"1e3", 1e3),
            (u"1e-3", 1e-3),
            (u"1.e3", 1e3),
            (u"1.e-3", 1e-3),
            (u".5e3", 0.5e3),
            (u".5e-3", 0.5e-3),
            (u"1.5e3", 1.5e3),
            (u"1.5e-3", 1.5e-3),
        )
        def gen_signs():
            for item, value in numbers:
                yield (item, value)
                yield (u"+" + item, value)
                yield (u"-" + item, -value)

        self.check_numbers(gen_signs(), float)

    def test_parse_valid_identifiers(self):
        identifiers = (
            # Typical definition of identifiers.
            u"foo",
            u"ident-with-dashes",
            u"-leading-dash",
            u"trailing-dash-",
            u"ident_with_underscores",
            u"_leading_underscore",
            u"trailing_underscore_",
            u"ident.with.dots",
            # Unicode identifiers must work.
            u"☺",
            u"武術",
            u"空手",
            u"→",
            # Mixed.
            u"arrow→",
            u"Trømso",
            u"Güedángaños",
        )
        for item in identifiers:
            ident = self.parser(item).parse_identifier()
            self.assertEquals(item, ident)
            self.assertTrue(isinstance(ident, six.text_type))

    def check_strings(self, strings, type_):
        for item in strings:
            if isinstance(item, tuple):
                item, expected = item
            else:
                expected = item
            value = self.parser(u"\"" + item + u"\"").parse_string()
            self.assertEquals(expected, value)
            self.assertTrue(isinstance(value, type_))

    def test_parse_valid_strings(self):
        strings = (
            u"",
            u"this is a string",
            u" another with leading space",
            u"yet one more with trailing space ",
            u"unicode: this → that, Trømso, Java™, ☺",
            (u"escaped backslash: \\\\", u"escaped backslash: \\"),
            (u"escaped double quote: \\\"", u"escaped double quote: \""),
            (u"escaped UTF-8: \\☺", u"escaped UTF-8: ☺"),
        )
        self.check_strings(strings, six.text_type)

    def test_parse_valid_arrays(self):
        arrays = (
            (u"[]", []),
            (u"[ ]", []),
            (u"[1]", [1]),
            (u"[ 1]", [1]),
            (u"[1 ]", [1]),
            (u"[ 1 ]", [1]),
            (u"[1 2]", [1, 2]),
            (u"[ 1 2]", [1, 2]),
            (u"[1 2 ]", [1, 2]),
            (u"[ 1 2 ]", [1, 2]),
        )
        for item, expected in arrays:
            value = self.parser(item).parse_value()
            self.assertTrue(isinstance(value, list))
            self.assertListEqual(expected, value)
            # Replacing the spaces with newlines should work as well.
            value = self.parser(item.replace(" ", "\n")).parse_value()
            self.assertTrue(isinstance(value, list))
            self.assertListEqual(expected, value)

    def test_parse_invalid_numbers(self):
        invalid_numbers = (
            u"", u"-", u"+", u"-+", u"a", u"☺", u"-.", u".", u"e", u".e",
            u"+e", u"-e", u"-.e", u"+.e", u"e+", u"e-", u".-e", u".+e",
            u"--", u"++", u"+1e3.", u"..1", u"1.2.", u"1..2", u"\"foo\"",
            u"True", u"False", u"{}", u"[]", u"()", u"0xx00", "0.1AeA3",
            "-0x3", "-032", u"ee", u"1ee", u"1e1e1", u"0.1x2", u"1x.0",
        )
        for item in invalid_numbers:
            with self.assertRaises(wcfg.ParseError):
                self.parser(item).parse_number()

    def test_parse_invalid_booleans(self):
        invalid_booleans = (
            u"Tr", u"TRUE", u"TrUe", u"TruE", u"TrUE",
            u"Fa", u"FALSE", u"FaLSE", u"FaLsE", u"FalsE",
            u"1", u"0", u"\"True\"", u"\"False\"",
        )
        for item in invalid_booleans:
            with self.assertRaises(wcfg.ParseError):
                self.parser(item).parse_bool()

    def test_parse_invalid_strings(self):
        invalid_strings = (
            u"\"",     # Unterminated.
            u"\"a",    # Ditto.
            u"\"\\\"", # Ditto.
        )
        for item in invalid_strings:
            with self.assertRaises(wcfg.ParseError):
                self.parser(item).parse_string()


class TestDump(unittest.TestCase):

    @staticmethod
    def dump_value(value):
        stream = six.BytesIO()
        wcfg._dump_value(value, stream, 0)
        return stream.getvalue()

    def test_dump_values(self):
        values = (
            (True, b"True"),
            (False, b"False"),
            (123, b"123"),
            (-123, b"-123"),
            (0xFF, b"255"),  # An hex literal in Python is still an integer.
            (0o5, b"5"),     # Ditto for octals in Python.
            (0.5, b"0.5"),
            (-0.5, b"-0.5"),
            (six.b("byte string"), b'"byte string"'),
            (u"a string", b'"a string"'),
            (u"double quote: \"", b'"double quote: \\""'),
            ((1, 2, 3), b"[\n  1\n  2\n  3\n]"),
            ([1, 2, 3], b"[\n  1\n  2\n  3\n]"),
            ({"a": 1, "b": 2}, b"{\n  a: 1\n  b: 2\n}"),
        )
        for value, expected in values:
            result = self.dump_value(value)
            self.assertEquals(expected, result)
            self.assertTrue(isinstance(result, bytes))

    def test_invalid_key_types(self):
        invalid_keys = (
            42, 3.14,    # Numeric.
            object(),    # Objects.
            object,      # Classes.
            True, False, # Booleans.
            [], (), {},  # Collections.
        )
        for key in invalid_keys:
            with self.assertRaises(TypeError):
                wcfg.dumps({ key: True })

    def test_invalid_key_values(self):
        invalid_keys = (
            "col:on",    # Colons are not allowed.
            "sp ace",    # Ditto for spaces.
        )
        for key in invalid_keys:
            with self.assertRaises(ValueError):
                wcfg.dumps({ key: True })

    def test_dump_non_dict(self):
        invalid_values = (
            "string",
            42, 3.14,    # Numbers.
            object(),    # Objects.
            object,      # Classes.
            True, False, # Booleans.
            [], (),      # Non-dict collections.
        )
        for value in invalid_values:
            with self.assertRaises(TypeError):
                wcfg.dumps(value)

    def test_invalid_values(self):
        invalid_values = (
            object(),    # Objects.
            object,      # Classes.
        )
        for value in invalid_values:
            with self.assertRaises(TypeError):
                wcfg.dumps({ "value": value })


class TestAPI(unittest.TestCase):

    TEST_VALUES = (
        ({}, ""),
        ({"a": 1, "b": 2}, """\
            a: 1
            b: 2
            """),
        ({"a": {"b": {}}}, """\
            a: {
              b: {
              }
            }
            """),
        ({"a": {"t": True}, "nums": [1e4, -2, 0xA], "f": False}, """\
            a: {
              t: True
            }
            f: False
            nums: [
              10000.0
              -2
              10
            ]
            """),
        ({"a": [{"b": 1}, [1, 2, 3]]}, """\
            a: [
              {
                b: 1
              }
              [
                1
                2
                3
              ]
            ]
            """),
    )

    TEST_VALUES_LOADS_ONLY = (
        ({}, "# This only has a comment"),
        ({"list": [1, 2, 3]}, "list:[1 2 3]"),
        ({"list": [1, 2, 3]}, "list: [ 1 2 3 ]"),
        ({"list": [1, 2, 3]}, """\
            # Leading comment
            list: [1 2 3] # Inline comment
            # Trailing comment
            """),
        ({"list": [1, 2, 3]}, """\
            # This skips the optional colon
            list [
                1 2 3
            ]"""),
    )

    def get_dumps_test_values(self):
        for item in self.TEST_VALUES:
            yield item

    def get_loads_test_values(self):
        for item in self.TEST_VALUES:
            yield item
        for item in self.TEST_VALUES_LOADS_ONLY:
            yield item

    def test_dumps(self):
        for value, expected in self.get_dumps_test_values():
            result = wcfg.dumps(value)
            expected = six.b(dedent(expected))
            self.assertEquals(expected, result)
            self.assertTrue(isinstance(result, bytes))

    def test_loads(self):
        for expected, value in self.get_loads_test_values():
            result = wcfg.loads(six.b(dedent(value)))
            self.assertTrue(isinstance(result, dict))
            self.assertDictEqual(expected, result)
            # Passing Unicode text should work as well.
            result = wcfg.loads(dedent(value))
            self.assertTrue(isinstance(result, dict))
            self.assertDictEqual(expected, result)
