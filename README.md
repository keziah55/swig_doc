# SWIG Doc

Project to transform [SWIG](https://www.swig.org/) 
[html](https://github.com/swig/swig/tree/master/Doc/Manual)
documentation into Markdown and then render with
[zensical](https://zensical.org/).

Check out a preview on the [pages](https://keziah55.github.io/swig_doc/)
site for this repo.

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
versions of SWIG checked out, e.g.
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