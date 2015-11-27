==============
Advanced Usage
==============

Annotations
===========

Annotations are supported as defined in `HEP-1: Value Annotations
<https://github.com/aperezdc/hipack/blob/gh-pages/heps/hep-001.rst>`__. By
default, the parser accepts and validate annotations, but they are *not*
passed to the user. Conversely, dumping values does *not* write any
annotations by default.  In order to make use of parsed annotations a
“cast callback” must be provided, and to write annotations a “value
callback”.

Cast Callbacks
--------------

A “cast callback” is any callable object which will be called by the parser
every time it has ended parsing a value, and accepts the following arguments:

* A set of annotations.
* The text representation of a parsed value.
* The parsed value, converted to irs corresponding Python type.

The function must return a value, which can be either the same provided by the
parser or any other value. The result returned from :func:`hipack.load()` (or
:func:`hipack.loads()` contains the values returned by the cast function
*instead of the ones originally seen by the parser*. The main use case for
a cast callback is to convert HiPack values on-the-fly into objects of the
application domain, optinally making use of annotations to help the cast
function determine which kind of conversion to perform.

As en example, consider a simple contacts application which stores the
information of each contact in a file like the following::

    name "Peter"
    surname "Parker"
    instant-messaging [
        :xmpp "spiderman@marvel.com"
        :skype "spideysenses"
    ]
    ...

Note how the items inside the ``instant-messaging`` list are annotated with
the kind of instant messaging service they correspond to. When parsing a
file like this, we probably want to use the following classes to represent the
data above:

.. code-block:: python

    class Contact(object):
        def __init__(self, name, surname=u"", im=None):
            self.name = name
            self.surname = surname
            self.im = [] if im is None else im

    class IMAccount(object):
        kind = None
        def __init__(self, address):
            self.address = address

    class XMPPAccount(IMAccount):
        kind = "XMPP"

    class SkypeAccount(IMAccount):
        kind = "Skype"

Now, with those classes in place, we can write our cast function as follows:

.. code-block:: python

    def contacts_cast(annotations, stringvalue, value):
        if u"xmpp" in annotations:
            return XMPPAccount(value)
        elif u"skype" in annotations:
            return SkypeAccount(value)
        else:
            return value

Finally, we can load a contact file as follows:

    >>> with open("contact.hipack", "r") as f:
    ...     contact = Contact(**hipack.load(f, cast=contacts_cast))
    ...
    >>> isinstance(contact, Contact)
    True
    >>> isinstance(contact.im[0], XMPPAccount)
    True
    >>> contact.name, contact.im[0].address
    (u'Peter', u'spiderman@marvel.com')

Note that cast callbacks receive a set containing *all* the annotations
attached to a value, *including intrinsic implicit annotations*. This means
that every time the callback is invoked, there will be at least always the
intrinsic annotation which informs of the type of the value (``.int``,
``.float``, ``.list``, etc).


Value Callbacks
---------------

A “value callback” performs the opposite operation to `cast callbacks`_: it is
called when before serializing a value into its HiPack representation to give
the application an opportunity to convert arbitrary Python objects, and attach
annotations to the serialized value. Value callbacks must accept a Python
object as its first argument, and return two values:

* A basic value for which HiPack specifies a representation.
* An iterable which yields the annotations to attach to the value, or ``None``
  if the value has no annotations associated to it.

Continuing with the contacts example above, we can define a value callback
like the following to allow direct serialization of ``IMAccount`` objects:

.. code-block:: python

    def contact_value(obj):
        if isinstance(obj, IMAccount):
            return obj.address, (obj.kind.lower(),)
        else:
            return obj, None

Value callbacks are used in a way similar to cast callbacks, passing them to
the :func:`hipack.dump()` function. For example:

    >>> print(hipack.dumps({
    ...     "work-im": XMPPAccount("spiderman@marvel.com"),
    ...     "home-im": SkypeAccount("spideysenses"),
    ... }, value=contact_value)
    ...
    home-im::skype "spideysenses"
    work-im::xmpp "spiderman@marvel.com"

