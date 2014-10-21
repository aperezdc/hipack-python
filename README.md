wcfg
====

`wcfg` is a small module to parse hierarchical data from text files, and it
is particularly suitable for configuration files.

Features:

* Text-based, hierarchical format, with simple syntax which is designed to
  be easy to parse both by programs and humans.

* Both reading *and* writing back is supported. Written data is guaranteed
  to be readable back to its original representation.

* Small, self-contained, pure Python implementation.


Grammar
-------

This is the grammar accepted by the parser, in [EBNF
syntax](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_Form):

    identifier = - ( whitespace | ":" )

    string character = - "\""

    key-value pair = identifier, ":", value
                   | identifier, value

    octal digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7"

    digit = octal digit | "8" | "9"

    hexdigit = digit | "a" | "b" | "c" | "d" | "e" | "f"
                     | "A" | "B" | "C" | "D" | "E" | "F"

    sign = "-" | "+"

    integral number = digit, { digit }

    dotted float = ".", digit, { digit }
                 | digit, ".", { digit }

    exponent = ("e" | "E"), sign, digit, { digit }
             | ("e" | "E"), digit, { digit }

    float number = dotted float
                 | dotted float, exponent
                 | integral number, exponent

    number body = integral number
                | float number

    number = "0", ( "x" | "X" ), hex digit, { hex digit }
           | "0", octal digit, { octal digit }
           | sign, number body
           | number body

    value = "\"", { string character }, "\""
          | "[", { value } "]"
          | "{", { key-value pair }, "}"
          | number

    input = "{", { key-value pair }, "}"
          | { key-value pair }

Note that comments are not specified in the grammar above does not include
comments for the sake of simplicity. Comments can appear anywhere except
inside strings, and they span from the octothorpe sign (`#`) to the end of
the line.
