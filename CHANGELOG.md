# Change Log
All notable changes to this project will be documented in this file.

## [Unreleased]

## [v13] - 2016-03-21
### Added
- Allow serializing Python values of type `set` and `frozenset` as lists.

## [v12] - 2015-12-03
### Added
- API reference documentation now includes the `Parser` class.
- New `Parser.messages()` generator method, to easily iterate over multiple framed messages

### Fixed
- Frames messages in an input stream are now handled correctly when
  `Parser.parse_message()` is called repeatedly.
- Fixed typos in the documentation. (Patch by Óscar García Amor, <ogarcia@connectical.com>.)

## [v11] - 2015-12-02
### Fixed
- Fixed parsing of annotations after a dictionary key when whitespace is used
  as key separator.

## [v10] - 2015-11-27
### Added
- Documentation (using [Sphinx](http://sphinx-doc.org/). The generated documentation is available online [at Read The Docs](http://hipack-python.readthedocs.org/en/latest/).
- Support for [HEP-1: Value Annotations](https://github.com/aperezdc/hipack/blob/gh-pages/heps/hep-001.rst)

### Fixed
- Hex escape sequences in string literals no longer cause an error.

## v9 - 2015-07-26
- Added this changelog.

[Unreleased]: https://github.com/aperezdc/hipack-python/compare/v13...HEAD
[v13]: https://github.com/aperezdc/hipack-python/compare/v12...v13
[v12]: https://github.com/aperezdc/hipack-python/compare/v11...v12
[v11]: https://github.com/aperezdc/hipack-python/compare/v10...v11
[v10]: https://github.com/aperezdc/hipack-python/compare/v9...v10
