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
        return wcfg.Parser(six.BytesIO(six.b(string)))

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
            ("1", 1),
            ("+1", 1),
            ("-2", -2),
            ("123", 123),
            ("+123", 123),
            ("-123", -123),
        )
        self.check_numbers(numbers, six.integer_types)

    def test_parse_valid_hex_numbers(self):
        numbers = (
            ("0x1", 1),
            ("0X1", 1),
            ("0xcafe", 0xCAFE),
            ("0XCAFE", 0xCAFE),
            ("0xCAFE", 0xCAFE),
            ("0xCaFe", 0xCAFE),
            ("0x1234", 0x1234),
            ("0xC00FFEE", 0xC00FEE),
            ("0xdeadbeef", 0xdeadbeef),
        )
        self.check_numbers(numbers, six.integer_types)

    def test_parse_valid_octal_numbers(self):
        numbers = (
            ("01", 01),
            ("01234567", 01234567),
            ("042", 042),
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
            ident = self.parser(item.encode("utf-8")).parse_identifier()
            self.assertEquals(item, ident)
            self.assertTrue(isinstance(ident, six.text_type))

