#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014-2015, 2022 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

from setuptools import setup
from codecs import open
from os import path


def distrib_file(*relpath):
    try:
        return open(path.join(path.dirname(__file__), *relpath), "r", \
                encoding="utf-8")
    except IOError:
        class DummyFile(object):
            def read(self):
                return ""
        return DummyFile()


def get_version():
    for line in distrib_file("hipack.py"):
        if line.startswith("__version__"):
            line = line.split()
            if line[0] == "__version__":
                return line[2]
    return None


def get_readme():
    return distrib_file("README.rst").read()


setup(
    name="hipack",
    version=get_version(),
    description="Serialization library or the HiPack interchange format",
    long_description=get_readme(),
    author="Adrian Perez de Castro",
    author_email="aperez@igalia.com",
    url="https://github.com/aperezdc/hipack-python",
    py_modules=["hipack"],
    scripts=["hipack"],
    license="Dual GPL3 / MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
    tests_require=["tox"],
)
