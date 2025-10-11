# Release Process

Steps for releasing new versions.

## Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Release Steps

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Build package
5. Test installation
6. Tag release
7. Push to PyPI

## Example

```bash
# Update version
# Edit pyproject.toml: version = "0.2.0"

# Run tests
pytest

# Build
python -m build

# Test
pip install dist/markdown_reallocator-0.2.0-py3-none-any.whl

# Tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Publish
python -m twine upload dist/*
```
