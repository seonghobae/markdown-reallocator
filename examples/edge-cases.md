# Edge Cases and Special Formatting

This document contains various edge cases to test the robustness of markdown processing.

## Tables

### Simple Table

| Feature | Status | Priority |
|---------|--------|----------|
| Preprocessing | ✅ Complete | High |
| Splitting | ✅ Complete | High |
| Search | ✅ Complete | Medium |
| Deduplication | ✅ Complete | Low |

### Complex Table with Alignment

| Left Aligned | Center Aligned | Right Aligned | Multi-word Header |
|:-------------|:--------------:|--------------:|:------------------|
| Cell 1 | Cell 2 | Cell 3 | Cell 4 |
| **Bold** | *Italic* | `Code` | [Link](https://example.com) |
| Longer content here | Short | 123.45 | More text |

### Table with Code

| Language | Example | Output |
|----------|---------|--------|
| Python | `print("Hello")` | Hello |
| JavaScript | `console.log("Hi")` | Hi |
| Bash | `echo "Test"` | Test |

## Nested Lists

### Deeply Nested Lists

1. First level item
   - Second level bullet
     - Third level bullet
       - Fourth level bullet
         - Fifth level (very deep!)
           - Sixth level
   - Another second level
2. Second first level
   1. Numbered sub-item
   2. Another numbered
      - Mixed bullet
      - Another mixed
        1. Numbered again
        2. More numbers

### Mixed List Types

- Bullet list
  1. Numbered sublist
  2. More numbers
     - Back to bullets
       1. Numbers again
         - And bullets again
- Top level bullet
  * Asterisk bullet
    + Plus bullet
      - Hyphen bullet

### Lists with Code Blocks

1. First step: Install dependencies
   ```bash
   pip install markdown-reallocator
   ```

2. Second step: Import modules
   ```python
   from markdown_reallocator import MarkdownPreprocessor
   preprocessor = MarkdownPreprocessor()
   ```

3. Third step: Process document
   - Load the file
   - Run preprocessing
   - Save results

## Code Blocks

### Multiple Languages

Python example:
```python
def process_markdown(content: str) -> str:
    """Process markdown content.

    This function handles **bold** and other formatting.
    """
    return content.strip()
```

JavaScript example:
```javascript
function processMarkdown(content) {
    // Handle **bold** text
    return content.trim();
}
```

Bash script:
```bash
#!/bin/bash
# Process all markdown files

for file in *.md; do
    echo "Processing $file"
    markdown-reallocator process "$file"
done
```

### Code Block with Special Characters

```python
# Special characters that might cause issues
REGEX_PATTERN = r'^\*\*(.+?)\*\*$'
ESCAPED_CHARS = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']

def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    for char in ESCAPED_CHARS:
        text = text.replace(char, f'\\{char}')
    return text
```

### Inline Code with Special Cases

This is `**not bold**` because it's in code. Also `*single asterisk*` and backticks: \`code\`.

Multiple cases: `<html>`, `[link]`, `{json}`, `$variable`, `@decorator`.

## Blockquotes

### Simple Blockquotes

> This is a blockquote with **bold text** and *italic text*.
> It can span multiple lines.

### Nested Blockquotes

> This is a quote
> > This is a nested quote
> > > This is deeply nested
> > > > Even deeper
>
> Back to first level

### Blockquotes with Code

> Here's how to use the library:
> ```python
> from markdown_reallocator import MarkdownPreprocessor
> preprocessor = MarkdownPreprocessor()
> ```
>
> This makes preprocessing easy!

## Special Formatting Cases

### Multiple Adjacent Bold Sections

**First bold section** immediately followed by **second bold section** and **third bold section**.

**Bold at start** middle text **bold at end**

### Mixed Emphasis

This has **bold**, *italic*, ***bold and italic***, ~~strikethrough~~, and `inline code`.

Combination: ***bold italic*** with **bold *italic inside*** and *italic **bold inside***.

### Escaped Characters

\*\*This should not be bold\*\*

\# This should not be a heading

\[This should not be a link\](https://example.com)

### Unicode and Emojis

Testing unicode: 你好 안녕하세요 こんにちは Привет مرحبا

Emojis in text: 🚀 💻 📝 ✅ ❌ ⚠️ 🔥 💡

### HTML in Markdown

<div style="color: red">
This is HTML content that might need special handling.
</div>

<table>
<tr><td>HTML table</td></tr>
</table>

<!-- HTML comment that should be handled -->

### URLs and Links

Auto-links: https://example.com and http://test.org

Reference links: [Link text][ref]

[ref]: https://example.com "Optional title"

Inline links: [Example](https://example.com) and [Link with **bold**](https://test.com)

Image links: ![Alt text](image.png) and ![Image with special chars !@#](path/to/img.jpg)

## Horizontal Rules

Three hyphens:

---

Three asterisks:

***

Three underscores:

___

## Ambiguous Bold Cases

**This is definitely a title**

This paragraph has **emphasis in the middle** that should stay bold.

**What about this?** Is it a title or emphasis?

The previous line is ambiguous - it's a complete sentence but also standalone bold.

**Short**

**A Properly Capitalized Title That Stands Alone**

someone might write **lowercase standalone** - probably not a title

## Edge Case: Empty Elements

Empty blockquote:
>

Empty code block:
```

```

Empty list items:
-
- Item 2
-

## Task Lists

- [x] Completed task
- [ ] Incomplete task
- [x] Another completed
  - [ ] Sub-task uncompleted
  - [x] Sub-task completed

## Footnotes

Here is some text with a footnote[^1].

Another footnote reference[^note].

[^1]: This is the first footnote.

[^note]: This is a named footnote with **bold** and `code`.

## Math (if supported)

Inline math: $E = mc^2$

Block math:
$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

## Definition Lists

Term 1
: Definition for term 1
: Another definition for term 1

Term 2
: Definition for term 2

## Abbreviations

The HTML specification is maintained by the W3C.

*[HTML]: Hyper Text Markup Language
*[W3C]: World Wide Web Consortium

## Multiple Blank Lines

This has


multiple


blank


lines


between


paragraphs.

## Line Breaks

This line has two spaces at the end
So it should break here
And here too

Alternative with backslash\
Should also break\
At these points

## Very Long Lines

This is an extremely long line that goes on and on and on without any breaks and might cause issues with certain parsers or display systems especially if they have line length limits or wrapping requirements and could potentially break formatting in unexpected ways when processed by different tools.

## Special Characters in Headings

### Heading with `code`

### Heading with **bold**

### Heading with *italic*

### Heading with [link](https://example.com)

### Heading with emoji 🚀

### Heading with math $x^2$

## Conclusion

This document covers numerous edge cases that a robust markdown processor should handle correctly. Each section tests different aspects of markdown parsing and formatting.
