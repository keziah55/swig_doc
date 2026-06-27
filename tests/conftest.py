import pytest


@pytest.fixture
def sample_html():
    """See `sample_md` for equivalent markdown."""

    return """
Sample text.
<hr>

<tt>file.py</tt>

<p>blah blah blah here's an<br /><i>unordered</i> <b>list</b>
<ul>
    <li>I'm an item</li>
    <li>I'm another item</li>
</ul>
text.</p>

<em>ordered</em> <strong>list</strong>

<ol>
    <li>I'm the <s>first</s> item</li>
    <li>I'm the second item</li>
</ol>

another <mark>unordered</mark> list
<ul>
    <li>I'm an item</li>
    <li>I'm another item</li>
</ul>

x<sup>2</sup>
H<sub>2</sub>O

Here's a <q>quote</q>

Here's a <blockquote>block quote,
starts here

over multiple lines</blockquote>
    """


@pytest.fixture
def sample_md():
    """Equivalent markdown for `sample_html`."""

    return """
Sample text.
---

`file.py`

<p>blah blah blah here's an

*unordered* **list**

- I'm an item
- I'm another item

text.</p>

*ordered* **list**


1. I'm the ~~first~~ item
1. I'm the second item


another ==unordered== list

- I'm an item
- I'm another item


x^2^
H~2~O

Here's a "quote"

Here's a 
> block quote,
> starts here
> 
> over multiple lines
    """
