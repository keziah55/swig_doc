from swig_doc.md_utils import transform_internal_link

import pytest


@pytest.mark.parametrize(
    "href, expected",
    [
        # urls that should be transformed
        ("SWIG.html", "SWIG"),
        ("Python.html#Python_nn8", "Python#Python_nn8"),
        # urls that should not be transformed
        ("#Python_nn8", "#Python_nn8"),
        ("www.google.com", None),
        ("#internal_link", None),
        ("https://www.swig.org#Python_nn8", None),
        ("http://www.swig.org#Python_nn8", None),
    ],
)
def test_transform_internal_link(href, expected):

    if expected is None:
        expected = href
    assert transform_internal_link(href) == expected
