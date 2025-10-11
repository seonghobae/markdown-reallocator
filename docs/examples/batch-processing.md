# Batch Processing

Process multiple markdown files efficiently.

## Shell Script Example

```bash
#!/bin/bash
for file in inputs/*.md; do
    markdown-reallocator preprocess "$file" --output "outputs/$(basename "$file")"
done
```

## Python Example

```python
from pathlib import Path
from markdown_reallocator.core import MarkdownPreprocessor

preprocessor = MarkdownPreprocessor()

for md_file in Path("inputs").glob("*.md"):
    markdown = md_file.read_text()
    clean = preprocessor.preprocess(markdown)
    output_file = Path("outputs") / md_file.name
    output_file.write_text(clean)
```
