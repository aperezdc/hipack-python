#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

from test.util import *
import unittest2
import hipack
import six
from textwrap import dedent


def make_tuples(sequence):
    for item in iter(sequence):
        if isinstance(item, tuple):
            yield item
        else:
            yield (item, item)

def wrap_strings(sequence):
    return ((u"\"" + x + u"\"", y) for (x, y) in iter(sequence))


class TestParser(unittest2.TestCase):

    @staticmethod
    def parser(string):
        return hipack.Parser(six.BytesIO(string.encode("utf-8")))

    def test_parse_valid_booleans(self):
        booleans = (
            (u"True", True),
            (u"true", True),
            (u"False", False),
            (u"false", False),
        )
        for item, expected in also_annotations(booleans):
            value = self.parser(item).parse_value()
            self.assertEqual(expected, value)
            self.assertTrue(isinstance(value, bool))

    def check_numbers(self, numbers, type_):
        for item, result in also_annotations(numbers):
            value = self.parser(item).parse_value()
            self.assertEqual(result, value)
            self.assertTrue(isinstance(value, type_))
            # Trailing whitespace must not alter the result.
            value = self.parser(item + " ").parse_value()
            self.assertEqual(result, value)
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
            (u"-0x3", -0x3),
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
            (u"-032", -0o32),
        )
        self.check_numbers(numbers, six.integer_types)

    def test_parse_valid_float_numbers(self):
        numbers = (
            (u"1.", 1.0),
            (u".5", 0.5),
            (u"0.1", 0.1),
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

    def test_parse_valid_keys(self):
        keys = (
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
        for item in keys:
            key = self.parser(item).parse_key()
            self.assertEqual(item, key)
            self.assertTrue(isinstance(key, six.text_type))

    def check_strings(self, strings, type_):
        for item, expected in also_annotations(wrap_strings(make_tuples(strings))):
            value = self.parser(item).parse_value()
            self.assertEqual(expected, value)
            self.assertTrue(isinstance(value, type_))

    def test_parse_valid_strings(self):
        strings = (
            u"",
            u"this is a string",
            u" another with leading space",
            u"yet one more with trailing space ",
            u"unicode: this → that, Trømso, Java™, ☺",
            (u"numeric: \\65\\5d\\5F", u"numeric: e]_"),
            (u"new\\nline", u"new\nline"),
            (u"horizontal\\tab", u"horizontal\tab"),
            (u"carriage\\return", u"carriage\return"),
            (u"escaped backslash: \\\\", u"escaped backslash: \\"),
            (u"escaped double quote: \\\"", u"escaped double quote: \""),
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
        for item, expected in also_annotations(arrays):
            value = self.parser(item).parse_value()
            self.assertTrue(isinstance(value, list))
            self.assertListEqual(expected, value)
            # Replacing the spaces with newlines should work as well.
            value = self.parser(item.replace(" ", "\n")).parse_value()
            self.assertTrue(isinstance(value, list))
            self.assertListEqual(expected, value)

    def test_parse_valid_arrays_with_commas(self):
        arrays = (
            (u"[1,]", [1]),        # Dangling commas are allowed.
            (u"[1,2]", [1, 2]),    # Spaces around commas are optional.
            (u"[1, 2]", [1, 2]),   # Space can be provided, of course...
            (u"[1 , 2]", [1, 2]),  # ...even on both sides
            (u"[1\n,2]", [1, 2]),  # Newlines and commas.
            (u"[1,\n2]", [1, 2]),  # Ditto.
            (u"[1\t,2]", [1, 2]),  # Tabs around commas.
            (u"[1,2,]", [1, 2]),   # More than one item and dangling comma.
            (u"[1, 2, ]", [1, 2]), # Spaces after dangling comma.
            (u"[1 2,3]", [1,2,3]), # Mixed spaces and commas.
        )
        for item, expected in also_annotations(arrays):
            value = self.parser(item).parse_value()
            self.assertTrue(isinstance(value, list))
            self.assertListEqual(expected, value)

    def test_parse_invalid_arrays(self):
        invalid_arrays = (
            u"[",      # Unterminated array.
            u"[1",     # Ditto.
            u"[1 2",   # Ditto.
            u"[[]",    # Unterminated inner array.
            u"(1)",    # Not an array.
            u"[:]",    # Invalid value inside array.
            u"[\"]",   # Unterminated string inside array.
            u"[\"]\"", # Unbalanced double-quote and brackets.
        )
        for item, _ in also_annotations(make_tuples(invalid_arrays)):
            with self.assertRaises(hipack.ParseError):
                self.parser(item).parse_value()

    @data(also_annotations((
        u"{ 0 }",
        u"{ foo: }",
        u"{ foo:foo }",
        u"{foo:0]", u"{ foo: 0 ]",
        u"{a{b{c}}}",
        u"{a,}",
        u"{a()}",
    )))
    def test_parse_invalid_dict(self, text):
        with self.assertRaises(hipack.ParseError):
            self.parser(text[0]).parse_value()

    @data(also_annotations((
        (u"{}", {}),
        (u"{a:1}", {"a":1}),
        (u"{a:1,b:2}", {"a":1, "b":2}),
        (u"{a{b{c{}}}}", {"a":{"b":{"c":{}}}}),
    )))
    def test_parse_valid_dict(self, data):
        text, expected = data
        value = self.parser(text).parse_value()
        self.assertEqual(expected, value)

    @data((
        u",", u"{", u"}", u"[", u"]", u"{]", u"[]", u"[}",
        u"{ a: 1 ]", u"{ a { foo: 1, ], ]", u"{a:1,,}",
    ))
    def test_parse_invalid_message(self, text):
        with self.assertRaises(hipack.ParseError):
            self.parser(text).parse_message()

    @data((
        u"value :annot 0",
        u"value :annot 1.1",
        u"value :annot True",
        u"value :annot []",
        u"value :annot {}",
    ))
    def test_parse_valid_message_with_annots(self, text):
        def check_annot(annotations, text, value):
            self.assertIn(u"annot", annotations)
            return value
        value = hipack.loads(six.b(text), check_annot)
        self.assertIsInstance(value, dict)

    def test_parse_invalid_arrays_with_commas(self):
        invalid_arrays = (
            u"[,]",     # Array with holes.
            u"[ ,]",    # Ditto.
            u"[, ]",    # Ditto.
            u"[,,]",    # Multiple holes.
            u"[\v,\t]", # Ditto.
            u"[,1]",    # Leading comma.
            u"[1,,]",   # Double trailing comma.
        )
        for item, _ in also_annotations(make_tuples(invalid_arrays)):
            with self.assertRaises(hipack.ParseError):
                self.parser(item).parse_value()

    def test_parse_invalid_numbers(self):
        invalid_numbers = (
            u"", u"-", u"+", u"-+", u"a", u"☺", u"-.", u".", u"e", u".e",
            u"+e", u"-e", u"-.e", u"+.e", u"e+", u"e-", u".-e", u".+e",
            u"--", u"++", u"+1e3.", u"..1", u"1.2.", u"1..2", u"\"foo\"",
            u"True", u"False", u"{}", u"[]", u"()", u"0xx00", "0.1AeA3",
            u"ee", u"1ee", u"1e1e1", u"0.1x2", u"1x.0", u"01.0", u"01e1",
            u"0x10.20",
        )
        for item, _ in also_annotations(make_tuples(invalid_numbers)):
            with self.assertRaises(hipack.ParseError):
                parser = self.parser(item)
                parser.parse_annotations()
                parser.parse_number(set())

    def test_parse_invalid_booleans(self):
        invalid_booleans = (
            u"Tr", u"TRUE", u"TrUe", u"TruE", u"TrUE",
            u"Fa", u"FALSE", u"FaLSE", u"FaLsE", u"FalsE",
            u"1", u"0", u"\"True\"", u"\"False\"",
        )
        for item, _ in also_annotations(make_tuples(invalid_booleans)):
            with self.assertRaises(hipack.ParseError):
                parser = self.parser(item)
                parser.parse_annotations()
                parser.parse_bool(set())

    def test_parse_invalid_strings(self):
        invalid_strings = (
            u"\"",       # Unterminated.
            u"\"a",      # Ditto.
            u"\"\\\"",   # Ditto.
            u"\"\\gg\"", # On-hex escape sequence.
        )
        for item, _ in also_annotations(make_tuples(invalid_strings)):
            with self.assertRaises(hipack.ParseError):
                parser = self.parser(item)
                parser.parse_annotations()
                parser.parse_string(set())

    def test_parse_invalid_annotations(self):
        invalid_annotations = (
            u":", u"::", u": :", u":a :", ":a:", u":a::",
            u":[", u":]", u":,", u":{", u":}", u".:foo",
            u":::", u":a::", u":a:b:",
            u":a :a",  # Duplicate annotation
        )
        for item in invalid_annotations:
            with self.assertRaises(hipack.ParseError):
                self.parser(item + u" 0").parse_value()

    @unittest2.skipUnless(six.PY3, "relevant only for Python 3.x")
    def test_python3_textwrap(self):
        from io import TextIOWrapper
        stream = six.BytesIO()
        wrapper = TextIOWrapper(stream)
        hipack.dump({"a": True}, wrapper)
        self.assertEqual(six.b("a: True\n"), stream.getvalue())


class TestDump(unittest2.TestCase):

    @staticmethod
    def dump_value(value):
        stream = six.BytesIO()
        hipack._dump_value(value, stream, 0, hipack.value)
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
            self.assertEqual(expected, result)
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
                hipack.dumps({ key: True })

    def test_invalid_key_values(self):
        invalid_keys = (
            "col:on",    # Colons are not allowed.
            "sp ace",    # Ditto for spaces.
        )
        for key in invalid_keys:
            with self.assertRaises(ValueError):
                hipack.dumps({ key: True })

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
                hipack.dumps(value)

    def test_invalid_values(self):
        invalid_values = (
            object(),    # Objects.
            object,      # Classes.
        )
        for value in invalid_values:
            with self.assertRaises(TypeError):
                hipack.dumps({ "value": value })

unpack_data(TestParser)


class TestAPI(unittest2.TestCase):

    TEST_VALUES = (
        ({}, "", ""),
        ({"a": 1, "b": 2},
            "a:1 b:2 ",
            """\
            a: 1
            b: 2
            """),
        ({"a": {"b": {}}},
            "a:{b:{} } ",
            """\
            a: {
              b: {
              }
            }
            """),
        ({"a": {"t": True}, "nums": [1e4, -2, 0xA], "f": False},
            "a:{t:True } f:False nums:[10000.0,-2,10,] ",
            """\
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
        ({"a": [{"b": 1}, [1, 2, 3]]},
            "a:[{b:1 },[1,2,3,],] ",
            """\
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
        for a, b, c in self.TEST_VALUES:
            yield a, b
            yield a, c
        for item in self.TEST_VALUES_LOADS_ONLY:
            yield item

    def test_dumps(self):
        for value, expected_noindent, expected \
                in self.get_dumps_test_values():
            result = hipack.dumps(value)
            expected = six.b(dedent(expected))
            self.assertEqual(expected, result)
            self.assertTrue(isinstance(result, bytes))
            expected_noindent = six.b(dedent(expected_noindent))
            result = hipack.dumps(value, False)
            self.assertEqual(expected_noindent, result)
            self.assertTrue(isinstance(result, bytes))

    def test_loads(self):
        for expected, value in self.get_loads_test_values():
            result = hipack.loads(six.b(dedent(value)))
            self.assertTrue(isinstance(result, dict))
            self.assertDictEqual(expected, result)
            # Passing Unicode text should work as well.
            result = hipack.loads(dedent(value))
            self.assertTrue(isinstance(result, dict))
            self.assertDictEqual(expected, result)
