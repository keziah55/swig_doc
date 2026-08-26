# SWIG Doc

Project to transform [SWIG](https://www.swig.org/) 
[html](https://github.com/swig/swig/tree/master/Doc/Manual)
documentation into Markdown and then render with
[zensical](https://zensical.org/).

Check out a preview on the [pages](https://keziah55.github.io/swig_doc/)
site for this repo.


## Dependencies

Install the core python dependencies in a virtual environment with
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

By default, `main.py` clones the [`swig`](https://github.com/swig/swig)
repo to a temporary directory.
To instead use locally checked out files, use the `-p` flag.


### Versions

By default, this tool creates docs for all 4.x versions, as well as the
HEAD of master branch.

To specify which branches/tags to checkout when building, use the `-v` arg.

Note that, currently, any version < 4 is not guaranteed to work.


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