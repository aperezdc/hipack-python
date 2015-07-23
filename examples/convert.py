#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

def load_hipack(fd):
    import hipack
    return hipack.load(fd)

def save_hipack(data, fd):
    import hipack
    hipack.dump(data, fd)

def save_hipack_compact(data, fd):
    import hipack
    hipack.dump(data, fd, indent=False)

def load_json(fd):
    import json
    return json.load(fd)

def save_json(data, fd):
    import json
    json.dump(data, fd)

def load_yaml(fd):
    import yaml
    return yaml.safe_load(fd)

def save_yaml(data, fd):
    import yaml
    yaml.safe_dump(data, fd)


formats = {
    "hipack":
        (load_hipack, save_hipack),
    "hipack-compact":
        (load_hipack, save_hipack_compact),
    "json":
        (load_json, save_json),
    "yaml":
        (load_yaml, save_yaml),
}


import optparse
parser = optparse.OptionParser("[-f format] [-t format] input output")
parser.add_option("-f", "--from", dest="from_format", default="json",
        help="Read input in the specified FORMAT", metavar="FORMAT")
parser.add_option("-t", "--to", dest="to_format", default="hipack",
        help="Write output in the specified FORMAT", metavar="FORMAT")
parser.add_option("--formats", default=False, action="store_true",
        help="Print list of supported formats and exit")

if __name__ == "__main__":
    import sys
    options, args = parser.parse_args()
    if options.formats:
        for name in sorted(formats.keys()):
            sys.stdout.write(name)
            sys.stdout.write("\n")
    else:
        try:
            load = formats[options.from_format][0]
        except KeyError:
            raise SystemExit("No such format: " + options.from_format)
        try:
            save = formats[options.to_format][1]
        except KeyError:
            raise SystemExit("No such format: " + options.to_format)

        save(load(sys.stdin), sys.stdout)