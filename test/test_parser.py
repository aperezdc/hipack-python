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


class TestParser(unittest.TestCase):

    @staticmethod
    def parser(string):
        return wcfg.Parser(six.BytesIO(string.encode("utf-8")))

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
