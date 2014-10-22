#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

"""This module provide a pythonic way to parse configuration files
used in libwheel
"""

__version__ = 2

import six
import string

_SPACE = six.b(" ")
_COLON = six.b(":")
_LBRACE = six.b("{")
_RBRACE = six.b("}")
_NEWLINE = six.b("\n")
_LBRACKET = six.b("[")
_RBRACKET = six.b("]")
_DQUOTE = six.b("\"")
_OCTOTHORPE = six.b("#")
_SLASHDQUOTE = six.b("\\\"")
_BACKSLASH = six.b("\\")
_NUMBER_SIGNS = six.b("+-")
_ZERO = six.b("0")
_HEX_X = six.b("xX")
_NUMBER_EXP = six.b("eE")
_DOT = six.b(".")
_EOF = six.b("")
_BOOL_LEADERS = six.b("tTfF")
_TRUE_T = six.b("tT")
_TRUE_RUE = (six.b("r"), six.b("u"), six.b("e"))
_FALSE_F = six.b("fF")
_FALSE_ALSE = (six.b("a"), six.b("l"), six.b("s"), six.b("e"))
_TRUE = six.b("True")
_FALSE = six.b("False")


whitespaces = six.b(string.whitespace)
_HEX_CHARS = six.b("abcdefABCDEF")
_NUMBER_CHARS = six.b(string.digits) + \
        _HEX_CHARS + _DOT + _NUMBER_EXP + _NUMBER_SIGNS + _HEX_X


def _dump_value(value, stream, indent):
    if isinstance(value, float):
        stream.write(str(value).encode("ascii"))
    elif isinstance(value, bool):
        stream.write(_TRUE if value else _FALSE)
    elif isinstance(value, six.integer_types):
        stream.write(str(value).encode("ascii"))
    elif isinstance(value, six.text_type):
        stream.write(_DQUOTE)
        stream.write(value.encode("utf-8").replace(_DQUOTE, _SLASHDQUOTE))
        stream.write(_DQUOTE)
    elif isinstance(value, six.string_types) or isinstance(value, bytes):
        stream.write(_DQUOTE)
        stream.write(value.replace(_DQUOTE, _SLASHDQUOTE))
        stream.write(_DQUOTE)
    elif isinstance(value, (tuple, list)):
        stream.write(_LBRACKET)
        for item in value:
            stream.write(_NEWLINE)
            stream.write(_SPACE * ((indent + 1) * 2))
            _dump_value(item, stream, indent + 1)
        stream.write(_NEWLINE)
        stream.write(_SPACE * (indent * 2))
        stream.write(_RBRACKET)
    elif isinstance(value, dict):
        stream.write(_LBRACE)
        stream.write(_NEWLINE)
        _dump_dict(value, stream, indent + 1)
        stream.write(_SPACE * (indent * 2))
        stream.write(_RBRACE)
    else:
        raise TypeError("Values of type " + str(type(value)) +
                        " cannot be dumped")


def _dump_dict(value, stream, indent):
    # Dictionaries are always dumped with their keys sorted,
    # in order to produce a predictible output.
    for k in sorted(six.iterkeys(value)):
        v = value[k]
        if isinstance(k, six.text_type):
            k = k.encode("utf-8")
        elif not isinstance(k, six.string_types):
            raise TypeError("Key is not a string: " + repr(k))
        if _COLON in k:
            raise ValueError("Key contains a colon: " + repr(k))
        if _SPACE in k:
            raise ValueError("Key contains a space: " + repr(k))
        stream.write(_SPACE * (indent * 2))
        stream.write(k)
        stream.write(_COLON)
        stream.write(_SPACE)
        _dump_value(v, stream, indent)
        stream.write(_NEWLINE)


def dump(value, stream):
    if not isinstance(value, dict):
        raise TypeError("Dictionary value expected")
    _dump_dict(value, stream, 0)


def dumps(value):
    output = six.BytesIO()
    dump(value, output)
    return output.getvalue()


class ParseError(ValueError):
    def __init__(self, line, column, message):
        super(ParseError, self).__init__(str(line) + ":" + str(column) +
                                         ": " + message)
        self.line = line
        self.column = column
        self.message = message


class Parser(object):
    def __init__(self, stream):
        self.look = None
        self.line = 1
        self.column = 0
        self.stream = stream
        self.getchar()

    def error(self, message):
        raise ParseError(self.line, self.column, message)

    def _basic_match(self, char, expected_message):
        if self.look != char:
            if expected_message is None:  # pragma: no cover
                expected_message = "character '" + str(char) + "'"
            self.error("Unexpected input '" + str(self.look) + "', " +
                    str(expected_message) + " was expected")
        self.getchar()

    def match(self, char, expected_message=None):
        self._basic_match(char, expected_message)
        self.skip_whitespace()

    def match_in(self, chars, expected_message=None):  # pragma: no cover
        if self.look not in chars:
            if expected_message is None:
                expected_message = "one of '" + str(chars) + "'"
            self.error("Unexpected input '" + str(self.look) + "', " +
                    str(expected_message) + " was expected")
        self.getchar()
        self.skip_whitespace()

    def match_sequence(self, chars, expected_message=None):
        for char in chars:
            self._basic_match(char, expected_message)
        self.skip_whitespace()

    def getchar(self):
        self.look = self.stream.read(1)
        if self.look == _EOF:
            return
        if self.look == _NEWLINE:
            self.column = 0
            self.line += 1
        self.column += 1
        # Skip over comments
        while self.look == _OCTOTHORPE:
            while self.look != _NEWLINE and self.look != _EOF:
                self.look = self.stream.read(1)
            self.column = 1
            self.line += 1
        # self.getchar()

    def skip_whitespace(self):
        while self.look != _EOF and self.look in whitespaces:
            self.getchar()

    def parse_identifier(self):
        identifier = six.BytesIO()
        while self.look != _COLON and self.look not in whitespaces:
            identifier.write(self.look)
            self.getchar()
        self.skip_whitespace()
        return identifier.getvalue().decode("utf-8")

    def parse_bool(self):
        if self.look in _TRUE_T:
            remaining = _TRUE_RUE
            ret = True
        elif self.look in _FALSE_F:
            remaining = _FALSE_ALSE
            ret = False
        else:
            self.error("True or False expected for boolean")
        self.getchar()
        self.match_sequence(remaining, _TRUE if ret else _FALSE)
        return ret

    def parse_string(self):
        value = six.BytesIO()
        char = self.stream.read(1)
        while char != _DQUOTE and char != _EOF:
            if char == _BACKSLASH:
                # A backslash picks the next character literally.
                char = self.stream.read(1)
            value.write(char)
            char = self.stream.read(1)
        if char != _DQUOTE:
            self.error("Unterminated string")
        self.getchar()
        self.skip_whitespace()
        return value.getvalue().decode("utf-8")

    def parse_number(self):
        number = six.BytesIO()

        # Optional sign.
        has_sign = False
        if self.look in _NUMBER_SIGNS:
            has_sign = True
            number.write(self.look)
            self.getchar()

        # Detect octal and hexadecimal numbers.
        is_hex = False
        is_octal = False
        if self.look == _ZERO:
            number.write(self.look)
            self.getchar()
            if self.look in _HEX_X:
                is_hex = True
                number.write(self.look)
                self.getchar()
            else:
                is_octal = True

        # Read the rest of the number.
        dot_seen = False
        exp_seen = False
        while self.look != _EOF and self.look in _NUMBER_CHARS:
            if self.look in _NUMBER_EXP and not is_hex:
                if exp_seen:
                    self.error("Malformed number at '" + str(self.look) + "'")
                exp_seen = True
                # Handle the optional sign of the exponent.
                number.write(self.look)
                self.getchar()
                if self.look in _NUMBER_SIGNS:
                    number.write(self.look)
                    self.getchar()
            else:
                if self.look == _DOT:
                    if dot_seen:
                        self.error("Malformed number at '" +
                                str(self.look) + "'")
                    dot_seen = True
                number.write(self.look)
                self.getchar()
        self.skip_whitespace()

        # Return number converted to the most appropriate type.
        number = number.getvalue().decode("ascii")
        try:
            if is_hex:
                assert not is_octal
                if exp_seen or dot_seen or has_sign:
                    raise ValueError(str(number))
                return int(number, 16)
            elif is_octal:
                assert not is_hex
                if dot_seen or exp_seen or has_sign:
                    raise ValueError(str(number))
                return int(number, 8)
            elif dot_seen or exp_seen:
                assert not is_hex
                assert not is_octal
                return float(number)
            else:
                assert not is_hex
                assert not is_octal
                assert not exp_seen
                assert not dot_seen
                return int(number)
        except ValueError:
            self.error("Malformed number: '" + str(number) + "'")

    def parse_value(self):
        value = None
        if self.look == _DQUOTE:
            value = self.parse_string()
        elif self.look == _LBRACE:
            self.match(_LBRACE)
            value = self.parse_keyval_items()
            self.match(_RBRACE)
        elif self.look == _LBRACKET:
            self.match(_LBRACKET)
            value = self.parse_array_items()
            self.match(_RBRACKET)
        elif self.look in _BOOL_LEADERS:
            value = self.parse_bool()
        else:
            value = self.parse_number()
        return value

    def parse_array_items(self):
        result = []
        while self.look != _EOF and self.look != _RBRACKET:
            result.append(self.parse_value())
        return result

    def parse_keyval_items(self):
        result = {}
        self.skip_whitespace()
        while self.look != _EOF and self.look != _RBRACE:
            key = self.parse_identifier()
            if self.look == _COLON:
                self.match(_COLON)
            self.skip_whitespace()
            result[key] = self.parse_value()
        return result


def load(stream):
    return Parser(stream).parse_keyval_items()


def loads(bytestring):
    if isinstance(bytestring, six.text_type):
        bytestring = bytestring.encode("utf-8")
    return load(six.BytesIO(bytestring))
