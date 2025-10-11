# Invalid Markdown Examples

This document contains intentionally malformed markdown.

## Unclosed Code Block

```python
def test():
    print("This code block is never closed"

## Mismatched Emphasis

**Bold starts but never ends

*Italic starts but never ends

***Triple emphasis with no close

## Broken Links

[Link with no URL]

[Link]( incomplete

![Image with no path]

## Malformed Headers

### ### Double hash

## No space after hash

##No space at all

## Broken Tables

| Header 1 | Header 2
|----------|
| Cell without closing pipe
| Another | Cell |

## Mixed Indentation

    Four spaces
  Two spaces
	Tab character
 One space

## Special Characters

\*\*\* Too many escapes \*\*\*

<<>> Angle brackets

{{{ Curly braces }}}

## Empty Elements

****

____

----

[]()

**

