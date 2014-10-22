#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2014 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPL3 license or, if that suits you
# better the MIT/X11 license.

from setuptools import setup
from os import path


def distrib_file(*relpath):
    try:
        return open(path.join(path.dirname(__file__), *relpath), "rU")
    except:
        class DummyFile(object):
            read = lambda self: ""
        return DummyFile()


def wcfg_version():
    for line in distrib_file("wcfg.py"):
        if line.startswith("__version__"):
            line = line.split()
            if line[0] == "__version__":
                return line[2]
    return None


def wcfg_readme():
    return distrib_file("README.md").read()


setup(
    name="wcfg",
    version=wcfg_version(),
    description="Parser for hyerarchical text data and configuration files",
    long_description=wcfg_readme(),
    author="Adrian Perez de Castro",
    author_email="aperez@igalia.com",
    url="https://github.com/aperezdc/python-wcfg",
    py_modules=["wcfg"],
    install_requires=["six>=1.8.0"],
    license="Dual GPL3 / MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ])
