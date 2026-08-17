# SWIG Doc

Project to transform [SWIG](https://www.swig.org/) 
[html](https://github.com/swig/swig/tree/master/Doc/Manual)
documentation into Markdown and then render with
[zensical](https://zensical.org/).

Check out a preview on the [pages](https://keziah55.github.io/swig_doc/)
site for this repo.


## Dependencies

Install the core python dependencies with
```
python -m pip install --group base
```

You can also install test and general development dependencies; see the groups listed
in [`pyproject.toml`](https://github.com/keziah55/swig_doc/blob/main/pyproject.toml).

`swig_doc` uses Python's built-in
[html parser](https://docs.python.org/3/library/html.parser.html)
to parse the html and generate markdown. However, 
[Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/)
is also a requirement, as it is used to validate the generated markdown
against the source html.


## Running

To generate a `docs` directory of markdown files:
```
python main.py
```

To build and view the docs:
```
zensical serve
```

To just build the docs, in `site` dir:
```
zensical build
```

### Using a local SWIG repo

By default, `main.py` downloads several [`swig`](https://github.com/swig/swig) branches.
To instead use locally checked out files, use the `-p` flag.

Note that this should point to a directory containing subdirs with different
versions of SWIG checked out, for example:
```
swig
├── latest
│   ├── CCache
│   ├── Doc
│   ├── Examples
│   ├── Lib
│   ├── Source
│   ├── Tools
│   └── Win
└── v4.5.0
    ├── CCache
    ├── Doc
    ├── Examples
    ├── Lib
    ├── Source
    ├── Tools
    └── Win
```

In this example, `latest` is the head of the master branch and `v4.5.0`
is the tag of the same name.


## Tests

Install test dependencies:
```
python -m pip install --group test
```

Run tests:
```
python -m pytest -v tests
```

Alternately, use the `nox` session:
```
nox --session tests
```
Note that this installs all the required dependencies in a standalone
virtual environment; however you do need to install `nox` first, e.g.
```
python -m pip install --group dev
```