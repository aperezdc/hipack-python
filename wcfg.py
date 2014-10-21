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

__version__ = 1

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
_BOOL = six.b("tTfF")
_TRUE = six.b("tT")
_FALSE = six.b("fF")

whitespaces = six.b(string.whitespace)
digits = six.b(string.digits)


def _dump_value(value, stream, indent):
    if isinstance(value, float):
        stream.write(str(float))
    elif isinstance(value, six.integer_types):
        stream.write(str(value))
    elif isinstance(value, six.text_type):
        stream.write(_DQUOTE)
        stream.write(value.encode("utf-8").replace(_DQUOTE, _SLASHDQUOTE))
        stream.write(_DQUOTE)
    elif isinstance(value, six.string_types):
        stream.write(_DQUOTE)
        stream.write(value.replace(_DQUOTE, _SLASHDQUOTE))
        stream.write(_DQUOTE)
    elif isinstance(value, (tuple, list)):
        stream.write(_LBRACKET)
        for item in value:
            stream.write(_NEWLINE)
            stream.write(_SPACE * (indent * 2))
            _dump_value(item, stream, indent)
        stream.write(_NEWLINE)
        stream.write(_SPACE * ((indent - 1) * 2))
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


def _dump_dict(value, stream, indent=0):
    for k, v in six.iteritems(value):
        if not isinstance(k, six.string_types):
            if isinstance(k, six.text_type):
                k = k.encode("utf-8")
            else:
                raise TypeError("Key is not a string: " + repr(k))
        if indent > 0:
            stream.write(_SPACE * (indent * 2))
        stream.write(k)
        stream.write(_SPACE)
        _dump_value(v, stream, indent + 1)
        stream.write(_NEWLINE)


def dump(value, stream):
    if not isinstance(value, dict):
        raise TypeError("Dictionary value expected")
    _dump_dict(value, stream)


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

    def match(self, char):
        if self.look != char:
            self.error("Character '" + str(char) + "' expected, got '"
                       + self.look + "' instead")
        self.getchar()
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
        return identifier.getvalue()

    def parse_bool(self):
        if self.look in _TRUE:
            ret = True
        elif self.look in _FALSE:
            ret = False
        else:
            self.error("True or False expected for boolean")
        while self.look != _NEWLINE and self.look != _EOF:
            self.getchar()
        return ret

    def parse_string(self):
        string = six.BytesIO()
        char = self.stream.read(1)
        while char != _DQUOTE and char != _EOF:
            if char == _BACKSLASH:
                # A backslash picks the next character literally.
                char = self.stream.read(1)
            string.write(char)
            char = self.stream.read(1)
        if char != _DQUOTE:
            self.error("Unterminated string")
        self.getchar()
        self.skip_whitespace()
        return string.getvalue().decode('utf-8')

    def parse_number(self):
        is_hex = False
        is_oct = False
        number = six.BytesIO()
        # Optional sign.
        has_sign = False
        if self.look in _NUMBER_SIGNS:
            has_sign = True
            number.write(self.look)
            self.getchar()
        # Detect octal and hexadecimal numbers.
        accepted_chars = digits + _DOT + _NUMBER_EXP
        if not has_sign and self.look == _ZERO:
            number.write(self.look)
            self.getchar()
            if self.look in _HEX_X:
                is_hex = True
                accepted_chars = six.b(string.hexdigits)
                number.write(self.look)
                self.getchar()
            else:
                is_oct = True
                accepted_chars = six.b(string.octdigits)

        # Read the rest of the number.
        dot_seen = False
        exp_seen = False
        while self.look != _EOF and self.look in accepted_chars:
            if self.look in _NUMBER_EXP:
                if exp_seen:
                    self.error("Malformed number")
                exp_seen = True
            elif self.look == _DOT:
                if dot_seen:
                    self.error("Malformed number")
                dot_seen = True
            number.write(self.look)
            self.getchar()
        # Return number converted to the most appropriate type.
        self.skip_whitespace()
        if is_hex:
            return int(number.getvalue(), 16)
        elif is_oct:
            return int(number.getvalue(), 8)
        elif dot_seen or exp_seen:
            return float(number.getvalue())
        else:
            return int(number.getvalue())

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
        elif self.look in _BOOL:
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
        while self.look != _EOF and self.look != _RBRACE:
            key = self.parse_identifier()
            if not key:
                continue
            if self.look == _COLON:
                self.match(_COLON)
            result[key.decode('utf-8')] = self.parse_value()
        return result


def load(stream):
    return Parser(stream).parse_keyval_items()


def dumps(value):
    output = six.BytesIO()
    dump(value, output)
    return output.getvalue()


def loads(bytestring):
    if isinstance(bytestring, six.text_type):
        bytestring = bytestring.encode("utf-8")
    return load(six.BytesIO(bytestring))
