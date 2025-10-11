"""Markdown preprocessor with bold-to-heading detection.

This module provides rule-based markdown normalization that detects
LLM-generated bold titles and converts them to proper headings.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PreprocessorConfig:
    """Configuration for markdown preprocessing.

    Attributes:
        max_title_length: Maximum character length for bold text to be
            considered a title (default: 80)
        require_empty_lines: Whether to require empty lines before/after
            bold titles (default: True)
        min_capitalization_ratio: Minimum ratio of uppercase letters to
            total letters for title detection (default: 0.1)
        detect_title_case: Whether to detect title case patterns
            (default: True)
        preserve_code_blocks: Whether to skip processing inside code blocks
            (default: True)
        preserve_lists: Whether to skip processing inside lists
            (default: True)
        preserve_tables: Whether to skip processing inside tables
            (default: True)
        log_ambiguous_cases: Whether to log warnings for ambiguous
            detections (default: True)
    """

    max_title_length: int = 80
    require_empty_lines: bool = True
    min_capitalization_ratio: float = 0.1
    detect_title_case: bool = True
    preserve_code_blocks: bool = True
    preserve_lists: bool = True
    preserve_tables: bool = True
    log_ambiguous_cases: bool = True

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if self.max_title_length < 1:
            raise ValueError(f"max_title_length must be positive, got {self.max_title_length}")
        if not 0 <= self.min_capitalization_ratio <= 1:
            raise ValueError(
                f"min_capitalization_ratio must be in [0, 1], got {self.min_capitalization_ratio}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "max_title_length": self.max_title_length,
            "require_empty_lines": self.require_empty_lines,
            "min_capitalization_ratio": self.min_capitalization_ratio,
            "detect_title_case": self.detect_title_case,
            "preserve_code_blocks": self.preserve_code_blocks,
            "preserve_lists": self.preserve_lists,
            "preserve_tables": self.preserve_tables,
            "log_ambiguous_cases": self.log_ambiguous_cases,
        }

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "PreprocessorConfig":
        """Create config from dictionary."""
        return cls(**config_dict)


class MarkdownPreprocessor:
    """Preprocessor for detecting and converting bold titles to headings.

    This class implements rule-based heuristics to distinguish between
    bold text used for titles (which should be headings) and bold text
    used for emphasis (which should remain as-is).

    Examples:
        >>> preprocessor = MarkdownPreprocessor()
        >>> markdown = "**Introduction**\\n\\nSome text here."
        >>> result = preprocessor.preprocess(markdown)
        >>> print(result)
        ## Introduction

        Some text here.
    """

    def __init__(self, config: PreprocessorConfig | None = None):
        """Initialize preprocessor with configuration.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or PreprocessorConfig()
        self._in_code_block = False
        self._in_list = False
        self._in_table = False
        self._heading_levels: list[int] = []  # Track heading levels seen

    def detect_bold_title(
        self,
        line: str,
        context: list[str],
        line_index: int
    ) -> bool:
        """Detect if bold text on a line is a title.

        Uses heuristics to distinguish title bold from emphasis bold:
        - Standalone on line (only whitespace around bold)
        - Empty lines before/after (or at document boundaries)
        - Line length within title threshold
        - Capitalization patterns (title case or first letter uppercase)

        Args:
            line: The line to check
            context: List of all lines in document
            line_index: Index of current line in context

        Returns:
            True if bold text appears to be a title
        """
        # Skip if in protected contexts
        if self.config.preserve_code_blocks and self._in_code_block:
            return False
        if self.config.preserve_lists and self._in_list:
            return False
        if self.config.preserve_tables and self._in_table:
            return False

        # Check if line contains bold pattern
        bold_pattern = re.compile(r'^\s*\*\*(.+?)\*\*\s*$')
        match = bold_pattern.match(line)

        if not match:
            return False

        bold_text = match.group(1)

        # Check length constraint
        if len(bold_text) > self.config.max_title_length:
            if self.config.log_ambiguous_cases:
                logger.warning(
                    f"Bold text exceeds max title length ({len(bold_text)} > "
                    f"{self.config.max_title_length}): {bold_text[:50]}..."
                )
            return False

        # Check empty lines before/after if required
        if self.config.require_empty_lines:
            has_empty_before = (
                line_index == 0 or
                context[line_index - 1].strip() == ""
            )
            has_empty_after = (
                line_index == len(context) - 1 or
                context[line_index + 1].strip() == ""
            )

            if not (has_empty_before and has_empty_after):
                return False

        # Check capitalization patterns
        letters = [c for c in bold_text if c.isalpha()]
        if not letters:
            return False

        # Check if first letter is uppercase (minimum requirement)
        first_char = next((c for c in bold_text if c.isalpha()), None)
        if not first_char or not first_char.isupper():
            return False

        # Check for title case if enabled (do this before ratio check)
        if self.config.detect_title_case:
            words = bold_text.split()
            if len(words) > 1:
                # Title case: most words start with uppercase
                title_case_count = sum(1 for word in words if word and word[0].isalpha() and word[0].isupper())
                title_case_ratio = title_case_count / len(words)

                # If it looks like title case, it's likely a title
                if title_case_ratio >= 0.5:
                    return True
            else:
                # Single word with first letter uppercase is likely a title
                # (given it passes other checks like empty lines)
                return True

        # For non-title-case detection or when title case disabled,
        # check capitalization ratio
        uppercase_count = sum(1 for c in letters if c.isupper())
        capitalization_ratio = uppercase_count / len(letters)

        if capitalization_ratio < self.config.min_capitalization_ratio:
            return False

        return True

    def infer_heading_level(
        self,
        context: list[str],
        line_index: int
    ) -> int:
        """Infer appropriate heading level from document context.

        Determines heading level (H2 or H3) based on surrounding structure:
        - Start with H2 if no headings seen yet
        - Use H3 if previous heading was H2
        - Avoid heading level jumps

        Args:
            context: List of all lines in document
            line_index: Index of current line in context

        Returns:
            Heading level (2 or 3)
        """
        # Look backwards for the most recent actual heading in context
        for i in range(line_index - 1, -1, -1):
            line = context[i].strip()
            if line.startswith("#"):
                # Count heading level
                level = len(line) - len(line.lstrip("#"))
                if level > 0:
                    # Next heading should be same level or one level deeper
                    return min(level + 1, 3)

        # If no headings found in context, use tracked headings
        if not self._heading_levels:
            # Default to H2 for first heading
            return 2

        # Get last tracked heading level
        last_level = self._heading_levels[-1]

        # Default progression: H2 → H3
        if last_level == 2:
            return 3

        return 2

    def convert_to_heading(
        self,
        bold_text: str,
        level: int
    ) -> str:
        """Convert bold text to markdown heading.

        Args:
            bold_text: The text inside bold markers
            level: Heading level (1-6)

        Returns:
            Markdown heading string

        Examples:
            >>> preprocessor = MarkdownPreprocessor()
            >>> preprocessor.convert_to_heading("Introduction", 2)
            '## Introduction'
        """
        if not 1 <= level <= 6:
            raise ValueError(f"Heading level must be 1-6, got {level}")

        heading_markers = "#" * level
        return f"{heading_markers} {bold_text}"

    def preprocess(self, markdown: str) -> str:
        """Preprocess markdown document.

        Main processing pipeline that:
        1. Splits markdown into lines
        2. Tracks context (code blocks, lists, tables)
        3. Detects bold titles and converts to headings
        4. Preserves all other markdown formatting

        Args:
            markdown: Input markdown string

        Returns:
            Processed markdown string
        """
        lines = markdown.split("\n")
        result_lines: list[str] = []

        # Reset state
        self._in_code_block = False
        self._in_list = False
        self._in_table = False
        self._heading_levels = []

        for i, line in enumerate(lines):
            # Track code block state
            if self.config.preserve_code_blocks:
                if line.strip().startswith("```"):
                    self._in_code_block = not self._in_code_block

            # Track list state
            if self.config.preserve_lists:
                list_pattern = re.compile(r'^\s*[-*+]\s+|\^\s*\d+\.\s+')
                self._in_list = bool(list_pattern.match(line))

            # Track table state
            if self.config.preserve_tables:
                self._in_table = "|" in line

            # Try to detect and convert bold title
            if self.detect_bold_title(line, lines, i):
                # Extract bold text
                match = re.match(r'^\s*\*\*(.+?)\*\*\s*$', line)
                if match:
                    bold_text = match.group(1)
                    level = self.infer_heading_level(lines, i)
                    converted = self.convert_to_heading(bold_text, level)

                    if self.config.log_ambiguous_cases:
                        logger.debug(
                            f"Converted bold to H{level}: {bold_text}"
                        )

                    result_lines.append(converted)
                    self._heading_levels.append(level)
                    continue

            # Track actual headings
            if line.strip().startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                if level > 0:
                    self._heading_levels.append(level)

            # Keep line as-is
            result_lines.append(line)

        return "\n".join(result_lines)
