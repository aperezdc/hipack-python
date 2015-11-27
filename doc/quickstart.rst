==========
Quickstart
==========

This guide will walk you through the usage of the Python :mod:`hipack` module.


Basic Usage
===========

The main use cases of the :mod:`hipack` module are to read and write messages
in `HiPack format <http://hipack.org>`__, and convert between the text-based
representation used in HiPack and the corresponding Python types.

The module defines functions to read (and write) HiPack-formatted messages
from strings and files:

* :func:`hipack.load()` parses a message from a file-like object.
* :func:`hipack.loads()` does the same, using a string as input.
* :func:`hipack.dump()` writes a message to a file-like object.
* :func:`hipack.dumps()` writes a message and returns it as a string.

Loading (deserialization)
-------------------------

Let's start parsing some data from a string which contains a HiPack message:

    >>> text = """\
    ... title: "Quickstart"
    ... is-documentation? True
    ... """
    >>> import hipack
    >>> value = hipack.loads(text)

HiPack messages are converted to dicionaries when parsing them, so now ``value``
contains a Python dictionary, and their values properly converted:

    >>> isinstance(value, dict)
    True
    >>> dict[u"title"], dict[u"is-documentation?"]
    (u'Quickstart", True)


Dumping (serialization)
-----------------------

The inverse operation, converting a Python dictionary to a HiPack message,
works in the expected way:

    >>> print(hipack.dumps(value))
    is-documentation?: True
    title: "Quickstart"'

Note how the output is nicely formatted. While that is desirable for human
consumption, some applications may want to make messages as small as possible,
and the module supports this by providing a setting to disable indentation and
unneeded spacing. Let's try now passing ``indent=False``:

    >>> print(hipack.dumps(value, indent=False))
    is-documentation?:False title:"Quickstart"


Framed messages
===============

Reading
-------

Using :meth:`hipack.Parser.parse_message()` to parse one message at a time,
it is possible to provide multiple messages chained, enclosed into braces,
in the same input. For example, consider the following input file, named
``heroes.hipack``::

    { name: "Spiderman", alter-ego: "Peter Parker" }
    { name: "Superman", alter-ego: "Clark Kent" }
    { name: "Batman", alter-ego: "Bruce Wayne" }

The following loop will iterate over the file, parsing and converting the
HiPack messages containing information about superheroes, one at a time,
and printing only their names (but not who is the person behind the mask):

    >>> with open("heroes.hipack", "r") as stream:
    ...     parser = hipack.Parser(stream)
    ...     while True:
    ...         hero = parser.parse_message()
    ...         if not hero:
    ...             break
    ...         print(hero[u"name"])
    ...
    Spiderman
    Superman
    Batman

Writing
-------

At the moment, there is no support to write messages *and* automatically add
the frame markers automatically in the module. Nevertheless, it is trivial to
write a loop which calls :func:`hipack.dump()` repeatedly and adds the braces
enclosing each message:

    >>> philosophers = (
    ...     {"name": "Karl Marx", "book": "The Capital"},
    ...     {"name": "Nietzsche", "book": "Thus Spoke Zarathustra"},
    ...     {"name": "Wittgenstein", "book": "Tractatus"},
    ... )
    >>> with open("philosophers.hipack", "w") as stream:
    ...    for item in philosophers:
    ...        stream.write("{\n")
    ...        hipack.dump(item, stream, indent=1)
    ...        stream.write("}\n")
    ...

Note how we pass ``indent=1`` above to indicate the initial level of
indentation, which gets us a nicely formatted ``philosophers.hipack`` file
with the following contents::

    {
      book: "The Capital"
      name: "Karl Marx"
    }
    {
      book: "Thus Spoke Zarathustra"
      name: "Nietzsche"
    }
    {
      book: "Tractatus"
      name: "Wittgenstein"
    }
