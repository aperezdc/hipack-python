#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014-2015, 2022 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

"""This module provide a pythonic way to handle HiPack messages.
"""

__version__ = 15
__heps__ = (1,)

import string
from io import BytesIO, TextIOWrapper

_SPACE = b" "
_COMMA = b","
_COLON = b":"
_LBRACE = b"{"
_RBRACE = b"}"
_TAB = b"\t"
_RETURN = b"\r"
_NEWLINE = b"\n"
_LBRACKET = b"["
_RBRACKET = b"]"
_DQUOTE = b"\""
_OCTOTHORPE = b"#"
_SLASHDQUOTE = b"\\\""
_BACKSLASH = b"\\"
_NUMBER_SIGNS = b"+-"
_ZERO = b"0"
_HEX_X = b"xX"
_NUMBER_EXP = b"eE"
_DOT = b"."
_EOF = b""
_BOOL_LEADERS = b"tTfF"
_TRUE_T = b"tT"
_TRUE_RUE = (b"r", b"u", b"e")
_FALSE_F = b"fF"
_FALSE_ALSE = (b"a", b"l", b"s", b"e")
_TRUE = b"True"
_FALSE = b"False"
_CHAR_n = b"n"
_CHAR_r = b"r"
_CHAR_t = b"t"


whitespaces = string.whitespace.encode("ascii")
_HEX_CHARS = b"abcdefABCDEF"
_HEX_DIGITS = b"0123456789" + _HEX_CHARS
_OCTAL_NONZERO_DIGITS = b"1234567"
_NUMBER_CHARS = string.digits.encode("ascii") + \
        _HEX_CHARS + _DOT + _NUMBER_EXP + _NUMBER_SIGNS + _HEX_X


# Those are defined according to the spec.
_WHITESPACE = b"\t\n\r "
_NON_KEY_CHARS = _WHITESPACE + b"[]{}:,"


# Intrinsic type annotations
ANNOT_INT = ".int"
ANNOT_FLOAT = ".float"
ANNOT_BOOL = ".bool"
ANNOT_STRING = ".string"
ANNOT_LIST = ".list"
ANNOT_DICT = ".dict"


def _is_hipack_key_character(ch):
    return ch not in _NON_KEY_CHARS


def _is_hipack_whitespace(ch):
    return ch in _WHITESPACE


def _dump_value(obj, stream, indent, value):
    if isinstance(obj, float):
        stream.write(str(obj).encode("ascii"))
    elif isinstance(obj, bool):
        stream.write(_TRUE if obj else _FALSE)
    elif isinstance(obj, int):
        stream.write(str(obj).encode("ascii"))
    elif isinstance(obj, str):
        stream.write(_DQUOTE)
        stream.write(obj.encode("utf-8").replace(_DQUOTE, _SLASHDQUOTE))
        stream.write(_DQUOTE)
    elif isinstance(obj, str) or isinstance(obj, bytes):
        stream.write(_DQUOTE)
        stream.write(obj.replace(_DQUOTE, _SLASHDQUOTE))
        stream.write(_DQUOTE)
    elif isinstance(obj, (tuple, list, set, frozenset)):
        stream.write(_LBRACKET)
        for item in obj:
            if indent >= 0:
                stream.write(_NEWLINE)
                stream.write(_SPACE * ((indent + 1) * 2))
                _dump_value(item, stream, indent + 1, value)
            else:
                _dump_value(item, stream, indent, value)
                stream.write(_COMMA)
        if indent >= 0:
            stream.write(_NEWLINE)
            stream.write(_SPACE * (indent * 2))
        stream.write(_RBRACKET)
    elif isinstance(obj, dict):
        stream.write(_LBRACE)
        if indent >= 0:
            stream.write(_NEWLINE)
            _dump_dict(obj, stream, indent + 1, value)
            stream.write(_SPACE * (indent * 2))
        else:
            _dump_dict(obj, stream, indent, value)
        stream.write(_RBRACE)
    else:
        raise TypeError("Values of type " + str(type(obj)) +
                        " cannot be dumped")


def _check_key(k, thing="Key"):
    if isinstance(k, str):
        k = k.encode("utf-8")
    elif not isinstance(k, str):
        raise TypeError(thing + " is not a string: " + repr(k))
    if _COLON in k:
        raise ValueError(thing + " contains a colon: " + repr(k))
    if _COMMA in k:
        raise ValueError(thing + " contains a comma: " + repr(k))
    if _SPACE in k or _NEWLINE in k or _RETURN in k or _TAB in k:
        raise ValueError(thing + " contains whitespace: " + repr(k))
    if _LBRACE in k or _RBRACE in k:
        raise ValueError(thing + " contains a brace: " + repr(k))
    if _LBRACKET in k or _RBRACKET in k:
        raise ValueError(thing + " contains a bracket: " + repr(k))
    return k


def _dump_dict(obj, stream, indent, value):
    # Dictionaries are always dumped with their keys sorted,
    # in order to produce a predictable output.
    for k in sorted(obj.keys()):
        v, annotations = value(obj[k])
        k = _check_key(k)
        stream.write(_SPACE * (indent * 2))
        stream.write(k)
        stream.write(_COLON)
        if annotations is not None and len(annotations) > 0:
            seen = set()
            for annot in iter(annotations):
                annot = _check_key(annot, "Annotation")
                if annot in seen:
                    raise ValueError("Duplicated annotation: " + repr(annot))
                seen.add(annot)
                stream.write(_COLON)
                stream.write(annot)
            stream.write(_SPACE)
        elif indent >= 0:
            stream.write(_SPACE)
        _dump_value(v, stream, indent, value)
        stream.write(_NEWLINE if indent >= 0 else _SPACE)


def value(obj):
    """
    Default “value” function.
    """
    return obj, None


def dump(obj, stream, indent=True, value=value):
    """
    Writes Python objects to a writable stream as a HiPack message.

    :param obj:
        Object to be serialized and written.
    :param stream:
        A file-like object with a `.write(b)` method.
    :param bool indent:
        Whether to pretty-print and indent the written message, instead
        of writing the whole message in single line. (Default: `False`).
    :param callable value:
        Function called before writing each value, which can perform
        additional conversions to support direct serialization of values other
        than those supported by HiPack. The function is passed a Python
        object, and it must return an object that can be represented as a
        HiPack value.
    """
    assert callable(value)
    obj, annotations = value(obj)
    if not isinstance(obj, dict):
        raise TypeError("Dictionary value expected")

    flush_after = False
    if isinstance(stream, TextIOWrapper):
        stream.flush()  # Make sure there are no buffered leftovers
        stream = stream.buffer
        flush_after = True

    _dump_dict(obj, stream, 0 if indent else -1, value)

    if flush_after:
        stream.flush()


def dumps(obj, indent=True, value=value):
    """
    Serializes a Python object into a string in HiPack format.

    :param obj:
        Object to be serialized and written.
    :param bool indent:
        Whether to pretty-print and indent the written message, instead
        of writing the whole message in single line. (Default: `False`).
    :param callable value:
        A Python object conversion function, see :func:`dump()` for details.
    """
    output = BytesIO()
    dump(obj, output, indent, value)
    return output.getvalue()


class ParseError(ValueError):
    """
    Use to signal an error when parsing a HiPack message.

    :attribute line:
        Input line where the error occurred.
    :attribute column:
        Input column where the error occured.
    :attribute message:
        Textual description of the error.
    """

    def __init__(self, line, column, message):
        super(ParseError, self).__init__(str(line) + ":" + str(column) +
                                         ": " + message)
        self.line = line
        self.column = column
        self.message = message


def cast(annotations, bytestring, value):
    """
    Default “cast” function.
    """
    return value


class Parser(object):
    """
    Parses HiPack messages and converts them to Python objects.

    :param stream:
        A file-like object with a `.read(n)` method.

    :param callable cast:
        Function called after each value has been parsed successfully, which
        can perform additional conversions on the data. The `cast` function
        is passed the set of annotations associated with the value, the
        `bytes` representation before converting a simple literal value (that
        is, all except lists and dictionaries, for which `None` is passed
        instead), and the converted value.
    """

    def __init__(self, stream, cast=cast):
        assert callable(cast)
        self.cast = cast
        self.look = None
        self.line = 1
        self.column = 0
        self.stream = stream
        self.nextchar()
        self.skip_whitespace()
        self.framed = (self.look == _LBRACE)

    def error(self, message):
        raise ParseError(self.line, self.column, message)

    def _basic_match(self, char, expected_message):
        if self.look != char:
            if expected_message is None:  # pragma: no cover
                expected_message = "character '" + str(char) + "'"
            self.error("Unexpected input '" + str(self.look) + "', " +
                       str(expected_message) + " was expected")
        self.nextchar()

    def match(self, char, expected_message=None):
        self._basic_match(char, expected_message)

    def match_sequence(self, chars, expected_message=None):
        for char in chars:
            self._basic_match(char, expected_message)

    def getchar(self):
        ch = self.stream.read(1)
        if ch == _EOF:
            return _EOF
        elif ch == _NEWLINE:
            self.column = 0
            self.line += 1
        self.column += 1
        return ch

    def nextchar(self):
        self.look = _OCTOTHORPE  # XXX Enter the loop at least once.
        while self.look == _OCTOTHORPE:
            self.look = self.getchar()
            if self.look == _OCTOTHORPE:
                while self.look not in (_EOF, _NEWLINE):
                    self.look = self.getchar()

    def skip_whitespace(self):
        while self.look != _EOF and _is_hipack_whitespace(self.look):
            self.nextchar()

    def parse_key(self):
        key = BytesIO()
        while self.look != _EOF and _is_hipack_key_character(self.look):
            key.write(self.look)
            self.nextchar()
        key = key.getvalue().decode("utf-8")
        if len(key) == 0:
            self.error("key expected")
        return key

    def parse_bool(self, annotations):
        s = self.look
        if self.look in _TRUE_T:
            remaining = _TRUE_RUE
            ret = True
        elif self.look in _FALSE_F:
            remaining = _FALSE_ALSE
            ret = False
        else:
            self.error("True or False expected for boolean")
        self.nextchar()
        self.match_sequence(remaining, _TRUE if ret else _FALSE)
        annotations.add(ANNOT_BOOL)
        return self.cast(frozenset(annotations), s.decode("utf-8"), ret)

    def parse_string(self, annotations):
        value = BytesIO()
        self.match(_DQUOTE)
        value.write(_DQUOTE)

        while self.look != _EOF and self.look != _DQUOTE:
            if self.look == _BACKSLASH:
                self.look = self.getchar()
                if self.look in (_DQUOTE, _BACKSLASH):
                    pass
                elif self.look == _CHAR_n:
                    self.look = _NEWLINE
                elif self.look == _CHAR_r:
                    self.look = _RETURN
                elif self.look == _CHAR_t:
                    self.look = _TAB
                else:
                    extra = self.getchar()
                    if extra not in _HEX_DIGITS or \
                            self.look not in _HEX_DIGITS:
                        self.error("invalid escape sequence")
                    self.look = (chr(16 * int(self.look, 16) + int(extra, 16))).encode("ascii")

            value.write(self.look)
            self.look = self.getchar()
        self.match(_DQUOTE)
        value.write(_DQUOTE)

        annotations.add(ANNOT_STRING)
        value = value.getvalue()
        return self.cast(frozenset(annotations), value, value[1:-1].decode("utf-8"))

    def parse_number(self, annotations):
        number = BytesIO()

        # Optional sign.
        if self.look in _NUMBER_SIGNS:
            number.write(self.look)
            self.nextchar()

        # Detect octal and hexadecimal numbers.
        is_hex = False
        is_octal = False
        if self.look == _ZERO:
            number.write(self.look)
            self.nextchar()
            if self.look in _HEX_X:
                is_hex = True
                number.write(self.look)
                self.nextchar()
            elif self.look in _OCTAL_NONZERO_DIGITS:
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
                self.nextchar()
                if self.look in _NUMBER_SIGNS:
                    number.write(self.look)
                    self.nextchar()
            else:
                if self.look == _DOT:
                    if dot_seen:
                        self.error("Malformed number at '" +
                                   str(self.look) + "'")
                    dot_seen = True
                number.write(self.look)
                self.nextchar()

        # Return number converted to the most appropriate type.
        number = number.getvalue().decode("ascii")
        value = None
        try:
            if is_hex:
                assert not is_octal
                if exp_seen or dot_seen:
                    raise ValueError(str(number))
                annotations.add(ANNOT_INT)
                value = int(number, 16)
            elif is_octal:
                assert not is_hex
                if dot_seen or exp_seen:
                    raise ValueError(str(number))
                annotations.add(ANNOT_INT)
                value = int(number, 8)
            elif dot_seen or exp_seen:
                assert not is_hex
                assert not is_octal
                annotations.add(ANNOT_FLOAT)
                value = float(number)
            else:
                assert not is_hex
                assert not is_octal
                assert not exp_seen
                assert not dot_seen
                annotations.add(ANNOT_INT)
                value = int(number, 10)
        except ValueError:
            self.error("Malformed number: '" + str(number) + "'")

        return self.cast(frozenset(annotations), number, value)

    def parse_dict(self, annotations):
        self.match(_LBRACE)
        self.skip_whitespace()
        result = self.parse_keyval_items(_RBRACE)
        self.match(_RBRACE)
        annotations.add(ANNOT_DICT)
        return self.cast(frozenset(annotations), None, result)

    def parse_list(self, annotations):
        self.match(_LBRACKET)
        self.skip_whitespace()

        result = []
        while self.look != _RBRACKET and self.look != _EOF:
            result.append(self.parse_value())

            got_whitespace = _is_hipack_whitespace(self.look)
            self.skip_whitespace()
            if self.look == _COMMA:
                self.nextchar()
            elif not got_whitespace and not _is_hipack_whitespace(self.look):
                break
            self.skip_whitespace()

        self.match(_RBRACKET)
        annotations.add(ANNOT_LIST)
        return self.cast(frozenset(annotations), None, result)

    def parse_annotations(self):
        annotations = set()
        while self.look == _COLON:
            self.nextchar()
            key = self.parse_key()
            if key in annotations:
                self.error("Duplicate annotation '" + str(key) + "'")
            annotations.add(key)
            self.skip_whitespace()
        return annotations

    def parse_value(self):
        value = None
        annotations = self.parse_annotations()
        # TODO: Unify annotation handling
        if self.look == _DQUOTE:
            value = self.parse_string(annotations)
        elif self.look == _LBRACE:
            value = self.parse_dict(annotations)
        elif self.look == _LBRACKET:
            value = self.parse_list(annotations)
        elif self.look in _BOOL_LEADERS:
            value = self.parse_bool(annotations)
        else:
            value = self.parse_number(annotations)
        return value

    def parse_keyval_items(self, eos):
        result = {}
        while self.look != eos and self.look != _EOF:
            key = self.parse_key()

            got_separator = False
            if _is_hipack_whitespace(self.look):
                got_separator = True
                self.skip_whitespace()
            elif self.look == _COLON:
                got_separator = True
                self.nextchar()
                self.skip_whitespace()
            elif self.look in (_LBRACE, _LBRACKET):
                got_separator = True

            if not got_separator:
                self.error("missing separator")

            result[key] = self.parse_value()

            # There must be either a comma or a whitespace character after the
            # value, or the end-of-sequence character.
            if self.look == _COMMA:
                self.nextchar()
            elif self.look != eos and not _is_hipack_whitespace(self.look):
                break
            self.skip_whitespace()

        return result

    def parse_message(self):
        """
        Parses a single message from the input stream. If the stream contains
        multiple messages delimited by braces, each subsequent calls
        will return the following message.
        """
        result = None
        if self.framed:
            if self.look != _EOF:
                self.match(_LBRACE)
                self.nextchar()
                self.skip_whitespace()
                result = self.parse_keyval_items(_RBRACE)
                self.match(_RBRACE)
                self.skip_whitespace()
        else:
            result = self.parse_keyval_items(_EOF)
        return result

    def messages(self):
        """
        Parses and yields each message contained in the input stream.

        For an input stream which contains a single, unframed message, the
        method yields exactly once. For an input with multiple, framed
        messages, each message is yield in the same order as they are in
        the input stream.
        """
        while True:
            message = self.parse_message()
            if message is None:
                break
            yield message


def load(stream, cast=cast):
    """
    Parses a single message from an input stream.

    :param stream:
        A file-like object with a `.read(n)` method.
    :param callable cast:
        A value conversion function, see :class:`Parser` for details.
    """
    return Parser(stream, cast).parse_message()


def loads(bytestring, cast=cast):
    """
    Parses a single message contained in a string.

    :param bytestring:
        Input string. It is valid to pass any of `str`, `unicode`, and `bytes`
        objects as input.
    :param callable cast:
        A value conversion function, see :class:`Parser` for details.
    """
    if isinstance(bytestring, str):
        bytestring = bytestring.encode("utf-8")
    return load(BytesIO(bytestring), cast)


if __name__ == "__main__":  ## pragma nocover
    import sys
    dump(load(sys.stdin), sys.stdout)
