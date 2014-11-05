====
wcfg
====

.. image:: https://drone.io/github.com/aperezdc/python-wcfg/status.png
   :target: https://drone.io/github.com/aperezdc/python-wcfg/latest
   :alt: Build Status

``wcfg`` is a small module to parse hierarchical data from text files, and it
is particularly suitable for configuration files.

Features:

* Text-based, hierarchical format, with simple syntax which is designed to
  be easy to parse both by programs and humans.

* Both reading *and* writing back is supported. Written data is guaranteed
  to be readable back to its original representation.

* Small, self-contained, pure Python implementation.

* Compatible with both Python 2.6 and 3.2 (or newer).


Example
=======

Given the following input file:

.. code-block:: yaml

  # Configuration file for SuperFooBar v3000
  interface {
    language: "en_US"
    panes {
      top: ["menu", "toolbar"]  # Optional commas in lists
      # The colon separating keys and values is optional
      bottom
        ["statusbar"]
    }
    ☺ : True  # Enables emoji
    Unicode→Suþþorteð? : "Indeed, Jürgen!"
  }

  # Configure plug-ins
  plugin: {
    preview  # Whitespace is mostly ignored
    {
      enabled: true
      timeout: 500  # Update every 500ms
    }
  }

Note that the ``:`` separator in between keys and values is optional, and
can be omitted. Also, notice how white space —including new lines— are
completely meaningless and the structure is determined using only braces
and brackets. Last but not least, a valid key is any Unicode character
sequence which *does not* include white space or a colon.

The following code can be used to read it into a Python dictionary:

.. code-block:: python

  import wcfg
  with open("superfoobar3000.conf", "rb") as f:
    config = wcfg.load(f)

Conversions work as expected:

* Sections are converted into dictionaries.
* Keys are converted conveted to strings.
* Text in double quotes are converted to strings.
* Sections enclosed into ``{ }`` are converted to dictionaries.
* Arrays enclosed into ``[ ]`` are converted to lists.
* Numbers are converted either to ``int`` or ``float``, whichever is more
  appropriate.
* Boolean values are converted to ``bool``.

The following can be used to convert a Python dictionary into its textual
representation:

.. code-block:: python

  users = {
    "peter": {
      "uid": 1000,
      "name": "Peter Jøglund",
      "groups": ["wheel", "peter"],
    },
    "root": {
      "uid": 0,
      "groups": ["root"],
    }
  }

  import wcfg
  text = wcfg.dumps(users)

When generating a textual representation, the keys of each dictionary will
be sorted, to guarantee that the generated output is stable. The dictionary
from the previous snippet would be written in text form as follows:

.. code-block:: yaml

  peter: {
    name: "Peter Jøglund"
    groups: ["wheel" "peter"]
    uid: 1000
  }
  root: {
    groups: ["root"]
    uid: 0
  }


Grammar
=======

This is the grammar accepted by the parser, in `EBNF syntax
<https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_Form>`__::

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

  boolean = "True" | "False"
          | "true" | "false"

  value = "\"", { string character }, "\""
        | "[", { (value | value ",") } "]"
        | "{", { key-value pair }, "}"
        | boolean
        | number

  input = "{", { key-value pair }, "}"
        | { key-value pair }

Note that comments are not specified in the grammar above does not include
comments for the sake of simplicity. Comments can appear anywhere except
inside strings, and they span from the octothorpe sign (``#``) to the end of
the line.
