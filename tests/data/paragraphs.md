
This chapter describes SWIG's support of Python.
This chapter covers most SWIG features, but certain low-level details
are covered in less depth than in earlier chapters.  At the
very least, make sure you read the "[SWIG Basics](SWIG.html#SWIG)" chapter.

## <a name="Python_nn2"></a> 33.1 Overview

SWIG is compatible
with all recent Python versions (Python 2.7 and Python >= 3.5).
SWIG-4.0 supported Python 3.2.  SWIG-3.0 supported older Python 2.x and 3.x.

To build Python extension modules, SWIG uses a layered approach in which
parts of the extension module are defined in C and other parts are
defined in Python.  The C layer contains low-level wrappers whereas Python code
is used to define high-level features.

