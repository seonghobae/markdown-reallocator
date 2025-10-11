# Preprocessing

The preprocessor fixes common structural issues in LLM-generated markdown, particularly converting bold-formatted titles to proper headings.

## Problem

LLMs frequently generate markdown with bold formatting instead of proper heading syntax:

```markdown
**Introduction**

This is the introduction section.

**Key Concepts**

Understanding these concepts is important.
```

This breaks:
- Document structure and navigation
- Table of contents generation
- Parsing by markdown tools
- Screen readers and accessibility

## Solution

The preprocessor detects and converts standalone bold lines to proper headings:

```markdown
## Introduction

This is the introduction section.

## Key Concepts

Understanding these concepts is important.
```

## Usage

### CLI

```bash
markdown-reallocator preprocess input.md --output clean.md
```

### Python API

```python
from markdown_reallocator.core.preprocessor import MarkdownPreprocessor

preprocessor = MarkdownPreprocessor()
markdown = open("input.md").read()
clean = preprocessor.preprocess(markdown)
```

## Detection Logic

The preprocessor uses multiple heuristics to distinguish title bold from emphasis bold:

1. **Empty lines**: Title candidates have empty lines before and after
2. **Length**: Titles are typically 3-80 characters
3. **Capitalization**: Titles have higher capital letter ratio
4. **Position**: First line or after empty line
5. **Content**: No inline formatting or special characters

### Example Detection

```markdown
# Detected as Title
**Introduction**

# Detected as Title  
**Getting Started Guide**

# Not a title (too long)
**This is a very long sentence that contains more than eighty characters and is clearly not a heading**

# Not a title (inline content)
This paragraph has **some bold text** for emphasis.

# Not a title (no empty lines)
**Bold**
Immediately followed by content.
```

## Configuration

Customize detection behavior:

```yaml
# config.yaml
preprocessor:
  max_title_length: 80
  require_empty_lines: true
  min_capitalization_ratio: 0.1
```

### Parameters

**max_title_length** (int, default: 80)
- Maximum character length for title candidates
- Longer bold text is treated as emphasis

**require_empty_lines** (bool, default: true)
- Require empty lines around title candidates
- Stricter but more accurate

**min_capitalization_ratio** (float, default: 0.1)
- Minimum proportion of capital letters
- Helps identify proper nouns and titles

## Examples

### Example 1: Basic Cleanup

**Input**:
```markdown
**Overview**

This document explains the API.

**Authentication**

Use OAuth 2.0 for authentication.
```

**Output**:
```markdown
## Overview

This document explains the API.

## Authentication

Use OAuth 2.0 for authentication.
```

### Example 2: Preserving Emphasis

**Input**:
```markdown
## Introduction

This is **very important** information.

You should **always** read the documentation.
```

**Output** (unchanged):
```markdown
## Introduction

This is **very important** information.

You should **always** read the documentation.
```

### Example 3: Mixed Content

**Input**:
```markdown
**Section 1**

Some text with **bold emphasis** in the middle.

**Section 2**

More content here.
```

**Output**:
```markdown
## Section 1

Some text with **bold emphasis** in the middle.

## Section 2

More content here.
```

## Advanced Usage

### Custom Configuration

```python
from markdown_reallocator.core.preprocessor import (
    MarkdownPreprocessor,
    PreprocessorConfig
)

config = PreprocessorConfig(
    max_title_length=100,
    require_empty_lines=False,
    min_capitalization_ratio=0.2
)

preprocessor = MarkdownPreprocessor(config)
result = preprocessor.preprocess(markdown)
```

### Validation

Check what will be converted:

```python
preprocessor = MarkdownPreprocessor()
markdown = "**Title**\n\nContent"

# Get statistics
stats = preprocessor.get_conversion_stats(markdown)
print(f"Found {stats['titles_found']} titles")
print(f"Will convert {stats['titles_converted']} to headers")
```

## Limitations

- Cannot detect semantic intent (sometimes bold is genuinely for emphasis)
- Relies on structural patterns (empty lines, length, etc.)
- May misclassify edge cases

For ambiguous cases, manual review is recommended.

## Next Steps

- [Splitting](splitting.md) - Create semantic chunks from preprocessed markdown
- [Configuration Guide](../getting-started/configuration.md) - Customize preprocessor behavior
