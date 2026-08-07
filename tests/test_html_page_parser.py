from swig_doc.html_parser import HtmlPageParser
from swig_doc.exceptions import EndTagWarning

import pytest


def test_convert_text_format(data_dir):

    fname = "convert_text_format"
    html_file = data_dir.joinpath(f"{fname}.html")
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    parser = HtmlPageParser(target_language="python")
    md = parser.parse(html_file)

    assert md == expected


def test_html_page_parser(data_dir):

    fname = "paragraphs"
    html_file = data_dir.joinpath(f"{fname}.html")
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    parser = HtmlPageParser(target_language="python")
    md = parser.parse(html_file)

    assert md == expected


def test_parse_list():
    html = """
<ul>
        <li>Download the swigwin zip package from the <a href="https://www.swig.org">SWIG website</a> and unzip into a directory. This is all that needs downloading for the Windows platform.
        <li>Set environment variables as described in the <a href="#Windows_examples">SWIG Windows Examples</a> section in order to run examples using Visual C++.
</ul>
"""  # noqa E501

    expected_md = """

- Download the swigwin zip package from the [SWIG website](https://www.swig.org) and unzip into a directory. This is all that needs downloading for the Windows platform.
- Set environment variables as described in the [SWIG Windows Examples](#Windows_examples) section in order to run examples using Visual C++.

"""  # noqa E501

    parser = HtmlPageParser()

    with pytest.warns(
        EndTagWarning,
        match=(
            r"End tag 'ul' encountered at \(\d, \d\); force close 'li' at pos " r"\(\d, \d\)"
        ),
    ):
        parser.feed(html)
    md = parser.doc

    assert md == expected_md


def test_parse_list_indented():

    html = """
<ol>
    <li>
        Install Nuget from <a href="https://www.nuget.org/downloads">https://www.nuget.org/downloads</a> (v6.0.0 is used in this example, and installed to <tt>C:\\Tools</tt>). Nuget is the package manager
        for .NET, but allows us to easily install <a href="https://cmake.org/">CMake</a> and other dependencies required by SWIG.
    </li>
    <li>
        Install <a href="https://www.nuget.org/packages/CMake-win64/">CMake-win64 Nuget package</a> using the following command: <pre>C:\\Tools\\nuget install CMake-win64 -Version 3.15.5 -OutputDirectory C:\\Tools\\CMake</pre>
        Using PowerShell the equivalent syntax is: <pre>&amp; "C:\\Tools\\nuget" install CMake-win64 -Version 3.15.5 -OutputDirectory C:\\Tools\\CMake</pre>
        Alternatively you can download CMake from <a href="https://cmake.org/download/">https://cmake.org/download/</a> or install a copy through your Visual Studio installer.
    </li>
    <li>
    <p>
        Now we have all the required dependencies we can build SWIG using PowerShell and the commands below. We are assuming Visual Studio 2019 or higher is installed and we will be building a 64-bit version of SWIG.
        For documentation on specific Visual Studio generators see the associated
        <a href="https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html#visual-studio-generators">Visual Studio Generators</a> documentation.
        We add the required build tools to the system <tt>PATH</tt> and then
        build a Release version of SWIG. If all runs successfully a new
        <tt>swig.exe</tt> should be generated in <tt>C:/swig/install2/bin</tt>.
    </p>
    </li>
</ol>
"""  # noqa E501

    expected_md = """

1. Install Nuget from [https://www.nuget.org/downloads](https://www.nuget.org/downloads) (v6.0.0 is used in this example, and installed to `C:\\Tools`). Nuget is the package manager
        for .NET, but allows us to easily install [CMake](https://cmake.org/) and other dependencies required by SWIG.
1. Install [CMake-win64 Nuget package](https://www.nuget.org/packages/CMake-win64/) using the following command: `C:\\Tools\\nuget install CMake-win64 -Version 3.15.5 -OutputDirectory C:\\Tools\\CMake`
        Using PowerShell the equivalent syntax is: `& "C:\\Tools\\nuget" install CMake-win64 -Version 3.15.5 -OutputDirectory C:\\Tools\\CMake`
        Alternatively you can download CMake from [https://cmake.org/download/](https://cmake.org/download/) or install a copy through your Visual Studio installer.
1. Now we have all the required dependencies we can build SWIG using PowerShell and the commands below. We are assuming Visual Studio 2019 or higher is installed and we will be building a 64-bit version of SWIG.
For documentation on specific Visual Studio generators see the associated
[Visual Studio Generators](https://cmake.org/cmake/help/latest/manual/cmake-generators.7.html#visual-studio-generators) documentation.
We add the required build tools to the system `PATH` and then
build a Release version of SWIG. If all runs successfully a new
`swig.exe` should be generated in `C:/swig/install2/bin`.

"""  # noqa E501

    parser = HtmlPageParser()
    parser.feed(html)
    md = parser.doc

    assert md == expected_md


def test_pre_multiple_class():

    html = """
<div class="code shell">
<pre>$ swig -ruby example.i
</pre>
</div>
"""

    expected_md = """
```shell
$ swig -ruby example.i

```
"""

    parser = HtmlPageParser()
    parser.feed(html)

    assert parser.doc == expected_md


def test_table():

    html = """
<TABLE summary="nickname table">
<TR><TD><B>usage</B></TD><TD><B>transform</B></TD></TR>
<TR><TD>"skip" tag</TD><TD>(none)</TD></TR>
<TR><TD>Examples/ subdir name</TD><TD>(none)</TD></TR>
<TR><TD>Examples/test-suite/ subdir name</TD><TD>(none)</TD></TR>
<!-- add more uses here (remember to adjust header) -->
</TABLE>
"""

    expected_md = """
| **usage** | **transform** | 
|---|---|
| "skip" tag | (none) | 
| Examples/ subdir name | (none) | 
| Examples/test-suite/ subdir name | (none) | 
<!-- add more uses here (remember to adjust header) -->

**Table:** nickname table
"""  # noqa W291

    parser = HtmlPageParser(quiet=False)
    parser.feed(html)

    assert parser.doc == expected_md


def test_table_with_th():

    html = """
<table class="tg"><thead>
  <tr>
    <th class="tg-0pky"><span style="font-weight:bold">**a**</span></th>
    <th class="tg-0pky"><span style="font-weight:bold">**b**</span></th>
    <th class="tg-0pky"><span style="font-weight:bold">**c**</span></th>
    <th class="tg-0pky"><span style="font-weight:bold">**d**</span></th>
  </tr></thead>
<tbody>
  <tr>
    <td class="tg-0pky">data</td>
    <td class="tg-0pky">hello</td>
    <td class="tg-0pky">escape \\| \\| char</td>
    <td class="tg-0pky">world</td>
  </tr>
  <tr>
    <td class="tg-0pky">aa</td>
    <td class="tg-0pky">bb</td>
    <td class="tg-0pky">cc</td>
    <td class="tg-0pky">dd</td>
  </tr>
  </tbody>
</table>
"""

    expected_md = """
| **a** | **b** | **c** | **d** | 
|---|---|---|---|
| data | hello | escape \\| \\| char | world | 
| aa | bb | cc | dd | 

"""  # noqa W291

    parser = HtmlPageParser()
    parser.feed(html)

    assert parser.doc == expected_md


def test_javadoc_table():

    html = """
<div class="diagram">
<table border="0" summary="Java Doxygen tags">
<tr>
  <th align="left">Doxygen tags</th>
</tr>
<tr>
<td>\\a</td>
<td>wrapped with &lt;i&gt; html tag</td>
<td>here's another
column</td>
</tr>
<tr>
<td>\\arg</td>
<td>wrapped with &lt;li&gt; html tag</td>
</tr>
</table>
</div>
"""

    expected_md = """

| Doxygen tags |  | |
|---|---|---|
| \\a | wrapped with <i\\> html tag | here's another column | 
| \\arg | wrapped with <li\\> html tag |  |

**Table:** Java Doxygen tags

"""  # noqa W291

    parser = HtmlPageParser()
    parser.feed(html)

    assert parser.doc == expected_md


def test_description_details():

    html = """
<p>Cryptids of Cornwall:</p>

<dl>
  <dt><b>Beast of Bodmin</b></dt>
  <dd>A large feline inhabiting Bodmin Moor.</dd>

  <dt><b>Morgawr</b></dt>
  <dd>A sea serpent.</dd>

  <dt><b>Owlman</b></dt>
  <dd>A giant owl-like creature.</dd>
</dl>
"""

    expected_md = """
Cryptids of Cornwall:

- **Beast of Bodmin**

    A large feline inhabiting Bodmin Moor.

- **Morgawr**

    A sea serpent.

- **Owlman**

    A giant owl-like creature.

"""

    parser = HtmlPageParser()
    parser.feed(html)

    assert parser.doc == expected_md


def test_description_details_paragraphs(data_dir):

    fname = "dl_paragraphs"
    html_file = data_dir.joinpath(f"{fname}.html")
    expected = data_dir.joinpath(f"{fname}.md").read_text()

    parser = HtmlPageParser(target_language="python")

    with pytest.warns(
        EndTagWarning,
        match=r"End tag 'dl' encountered at \(93, 0\); force close 'dd' at pos \(85, 0\)",
    ):
        md = parser.parse(html_file)

    assert md.strip() == expected.strip()


def test_leading_space_inline():

    html = "<b> What is received back by java.cxx </b>"
    expected_md = "**What is received back by java.cxx**"

    parser = HtmlPageParser()
    parser.feed(html)

    assert parser.doc == expected_md


def test_multiline_tt():
    html = """
<p>
<b><tt>PYTHON_INCLUDE</tt></b> : Set this to the directory that contains Python.h<br>
<b><tt>PYTHON_LIB</tt></b> : Set this to the Python library including path for linking<p>
Example using Python 3.13 installed in a Conda environment:<br>
<tt>
PYTHON_INCLUDE: C:\\miniconda3\\envs\\python\\include<br>
PYTHON_LIB: C:\\miniconda3\\envs\\python\\libs\\python313.lib<br>
</tt>
</p>
"""

    expected_md = """
**`PYTHON_INCLUDE`** : Set this to the directory that contains Python.h

**`PYTHON_LIB`** : Set this to the Python library including path for linking

Example using Python 3.13 installed in a Conda environment:

```
PYTHON_INCLUDE: C:\\miniconda3\\envs\\python\\include

PYTHON_LIB: C:\\miniconda3\\envs\\python\\libs\\python313.lib
```
"""

    parser = HtmlPageParser(quiet=False)
    parser.feed(html)

    assert parser.doc == expected_md


def test_close():

    html = """
<html>
<body>

<p>
This is a paragraph
</p>
"""

    expected_md = "\nThis is a paragraph\n"

    parser = HtmlPageParser()
    parser.feed(html)

    with pytest.warns(EndTagWarning, match=(r"force close 'body")):
        with pytest.warns(EndTagWarning, match=(r"force close 'html")):
            parser.close()

    assert parser.doc == expected_md


def test_html_table():

    html = """<table border="1" summary="Rewriting rules">
<tr><th>Input</th><th>Rewritten to</th></tr>
<tr><td>f'( ... ) as in<br> atoi'("0") or<br> _exit'(0)</td>
<td>f(C_list [ ... ]) as in<br> atoi (C_list [ C_string "0" ]) or<br> _exit (C_list [ C_int 0 ])</td></tr>
<tr><td>object -&gt; method ( ... )</td><td>(invoke object) "method" (C_list [ ... ])</td></tr>
<tr><td>
object <i>'binop</i> argument as in<br>
a '+= b</td>
<td>
(invoke object) "+=" argument as in<br>
(invoke a) "+=" b</td></tr>
<tr><th colspan=2>Note that because camlp4 always recognizes &lt;&lt;
and &gt;&gt;, they are replaced by lsl and lsr in operator names.
<tr><td>
<i>'unop</i> object as in<br>
'! a
</td><td>
(invoke a) "!" C_void</td></tr>
<tr><td>
<b>Smart pointer access like this</b><br>
object '-&gt; method ( args )<br>
</td><td>
(invoke (invoke object "-&gt;" C_void))
</td></tr>
</table>"""  # noqa E501

    parser = HtmlPageParser()
    parser.feed(html)

    expected = html.replace("\n", "")

    # when reconstructing html, attr values are always quoted
    # HtmlParser does not retain the quotes when passing into `handle_starttag`
    expected = expected.replace("colspan=2", 'colspan="2"')

    assert parser.doc.replace("\n", "") == expected
