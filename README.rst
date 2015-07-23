===============
 hipack-python
===============

.. image:: https://img.shields.io/travis/aperezdc/hipack-python.svg?style=flat
   :target: https://travis-ci.org/aperezdc/hipack-python
   :alt: Build Status

.. image:: https://img.shields.io/coveralls/aperezdc/hipack-python/master.svg?style=flat
   :target: https://coveralls.io/r/aperezdc/hipack-python?branch=master
   :alt: Code Coverage


``hipack`` is a Python module to work with the `HiPack <http://hipack.org>`_
serialization format. The API is intentionally similar to that of the standard
``json`` and ``pickle`` modules.

Features:

* Both reading, and writing HiPack is supported.

* Small, self-contained, pure Python implementation.

* Compatible with both Python 2.6 (or newer), and 3.2 (or newer).


Example
=======

Given the following input file:

.. code-block::

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

  import hipack
  with open("superfoobar3000.conf", "rb") as f:
    config = hipack.load(f)

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

  import hipack
  text = hipack.dumps(users)

When generating a textual representation, the keys of each dictionary will
be sorted, to guarantee that the generated output is stable. The dictionary
from the previous snippet would be written in text form as follows:

.. code-block::

  peter: {
    name: "Peter Jøglund"
    groups: ["wheel" "peter"]
    uid: 1000
  }
  root: {
    groups: ["root"]
    uid: 0
  }


