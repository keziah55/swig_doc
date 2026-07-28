

- **configure.ac**

    This file is processed by

    [autoconf](https://www.gnu.org/software/autoconf/)
    to generate the `configure` script.  This is where you
    need to add shell script fragments and autoconf macros to detect the
    presence of whatever development support your language module requires,
    typically directories where headers and libraries can be found, and/or
    utility programs useful for integrating the generated wrapper code.

    Use the `AC_ARG_WITH`, `AC_MSG_CHECKING`, `AC_SUBST`
    macros and so forth (see other languages for examples).  Avoid using the
    `[` and `]` character in shell script fragments.  The
    variable names passed to `AC_SUBST` should begin with the nickname,
    entirely upcased.

    At the end of the new section is the place to put the aforementioned
    nickname kludges (should they be needed).  See Perl5 for
    examples of what to do.  [If this is still unclear after you've read
    the code, ping me and I'll expand on this further.  --ttn]

- **Makefile.in**

    Some of the variables AC_SUBSTituted are essential to the
    support of your language module.  Fashion these into a shell script
    "test" clause and assign that to a skip tag using "-z" and "-o":

    ```
    skip-qux99 = [ -z "@QUX99INCLUDE@" -o -z "@QUX99LIBS" ]
    ```

    This means if those vars should ever be empty, qux99 support should
    be considered absent and so it would be a good idea to skip actions that
    might rely on it.

    Here is where you may also define an alias (but then you'll need to
    kludge --- don't do this):

    ```
    skip-qux = $(skip-qux99)
    ```

    Lastly, you need to modify each of `check-aliveness`,
    `check-examples`, `check-test-suite`
    and `lib-languages` (var).
    Use the nickname for these, not the alias.
    Note that you can do this even before you have any tests or examples
    set up; the Makefile rules do some sanity checking and skip around
    these kinds of problems.

- **Examples/Makefile.in**

    Nothing special here; see comments at the top of this file
    and look to the existing languages for examples.

- **Examples/qux99/check.list**

    Do `cp ../python/check.list .` and modify to taste.
    One subdir per line.

- **Lib/qux99/extra-install.list**

    If you add your language to the top-level Makefile.in var
    `lib-languages`, then `make install` will install
    all `*.i` and `*.swg` files from the language-specific
    subdirectory of `Lib`.  Use (optional) file
    `extra-install.list` in that directory to name
    additional files to install (see ruby for example).

- **Source/Modules/Makefile.am**

    Add appropriate files to this Automake file. That's it!

    When you have modified these files, please make sure that the new language module is completely
    ignored if it is not installed and detected on a box, that is, `make check-examples` and `make check-test-suite`
    politely displays the ignoring language message.
