# CLI Design Document

## Executive Summary

markdown-reallocator CLI는 마크다운 문서의 semantic chunking과 reallocation을 위한 커맨드라인 도구입니다. **Typer** 기반으로 구현하여 타입 안전성과 간결한 코드를 확보하고, Unix 철학에 따라 stdin/stdout을 지원합니다.

## 1. Technology Stack

### Core Framework: **Typer**

**선택 이유**:
- ✅ **타입 힌트 기반**: 이미 프로젝트가 완전한 타입 힌트 사용 (mypy 100% 통과)
- ✅ **최소 보일러플레이트**: Click보다 간결, argparse보다 직관적
- ✅ **자동 문서화**: 타입 힌트에서 help 메시지 자동 생성
- ✅ **현대적**: 2025년 Python CLI 표준으로 자리잡음
- ✅ **Click 기반**: Click의 검증된 기능 활용 (프롬프트, 서브커맨드)

**대안 비교**:

| Library | 장점 | 단점 | 선택 이유 |
|---------|------|------|----------|
| **Typer** | 타입 안전, 간결, 현대적 | 외부 의존성 | ✅ 타입 힌트와 완벽 호환 |
| Click | 검증됨, 널리 사용됨 | 보일러플레이트 많음 | ❌ Typer가 더 간결 |
| argparse | 표준 라이브러리, 의존성 없음 | 장황함, 구식 | ❌ 프로젝트 복잡도에 부적합 |

### Supporting Libraries
- **Rich**: 터미널 출력 포맷팅 (테이블, 진행바, 색상)
- **Pathlib**: 경로 처리 (표준 라이브러리)

## 2. Command Structure

### Unix Philosophy 원칙
1. **Do one thing well**: 각 커맨드는 하나의 명확한 작업 수행
2. **Composability**: 파이프라인 구성 가능 (stdin → stdout)
3. **Text streams**: JSON/Markdown 출력으로 다른 도구와 연계

### Command Hierarchy

```
markdown-reallocator
├── parse          # 마크다운 파싱 및 chunk 생성
├── analyze        # 문서 구조 분석
├── reallocate     # Chunk reallocation (유사도 기반 재배치)
└── validate       # 결과 검증
```

## 3. Command Specifications

### 3.1. `parse` - Markdown Parsing

**목적**: 마크다운 파일을 semantic chunks로 분할

**Usage**:
```bash
# 파일 파싱
markdown-reallocator parse input.md

# stdin에서 파싱
cat input.md | markdown-reallocator parse -

# 결과를 JSON으로 출력
markdown-reallocator parse input.md --format json > chunks.json

# 토큰 제한 설정
markdown-reallocator parse input.md --max-tokens 1000

# 특정 헤더 레벨만 분할 기준으로
markdown-reallocator parse input.md --split-headers h1,h2,h3
```

**Arguments**:
- `input_path` (Path | Literal["-"]): 입력 파일 경로 또는 "-" (stdin)

**Options**:
- `--max-tokens` (int, default=1024): Chunk당 최대 토큰 수
- `--format` (Literal["text", "json"], default="text"): 출력 형식
- `--split-headers` (str, default="h1,h2,h3"): 분할 기준 헤더 (쉼표 구분)
- `--output` / `-o` (Path, optional): 출력 파일 (기본: stdout)

**Output Format**:

**Text** (human-readable):
```
================================================================================
Document Structure Analysis
================================================================================

📊 Summary:
  Total chunks: 156
  Total tokens: 127,492
  Headers: h1=2, h2=15, h3=48

📁 Chunks by Type:
  narrative_text: 89
  list_item: 42
  code_snippet: 18
  header: 7

🔢 Token Statistics:
  Average: 817.3
  Min: 12
  Max: 1,024
  > 1000 tokens: 3 chunks

⚠️  Warnings:
  - Chunk 19: 1,234 tokens (exceeds limit)
  - Chunk 112: 1,189 tokens (exceeds limit)

================================================================================
Chunk Details
================================================================================

Chunk 1:
  ID: sha256:3a2f8b...
  Type: title
  Headers: h1=Introduction
  Tokens: 45
  Content:
    # Introduction

    This document describes...
```

**JSON** (machine-readable):
```json
{
  "summary": {
    "total_chunks": 156,
    "total_tokens": 127492,
    "header_counts": {"h1": 2, "h2": 15, "h3": 48},
    "element_counts": {
      "narrative_text": 89,
      "list_item": 42,
      "code_snippet": 18
    },
    "token_stats": {
      "average": 817.3,
      "min": 12,
      "max": 1024,
      "exceeds_limit": 3
    }
  },
  "chunks": [
    {
      "chunk_id": "sha256:3a2f8b...",
      "content": "# Introduction\n\nThis document...",
      "metadata": {
        "h1": "Introduction",
        "h2": null,
        "h3": null,
        "element_type": "title",
        "token_count": 45,
        "original_position": 0,
        "parent_id": null,
        "depth_level": 0,
        "sequence_number": null
      }
    }
  ]
}
```

### 3.2. `analyze` - Document Structure Analysis

**목적**: 문서 구조 심층 분석 (헤더 계층, 섹션 크기, 중복 탐지)

**Usage**:
```bash
# 기본 분석
markdown-reallocator analyze input.md

# 중복 탐지 포함
markdown-reallocator analyze input.md --detect-duplicates

# 섹션별 통계
markdown-reallocator analyze input.md --group-by h2

# JSON 출력
markdown-reallocator analyze input.md --format json
```

**Arguments**:
- `input_path` (Path | Literal["-"]): 입력 파일 경로 또는 "-" (stdin)

**Options**:
- `--detect-duplicates` (bool, default=False): 중복 콘텐츠 탐지
- `--similarity-threshold` (float, default=0.9): 중복 판정 유사도 임계값 (0.0-1.0)
- `--group-by` (Literal["h1", "h2", "h3"], optional): 섹션별 그룹화 기준
- `--format` (Literal["text", "json"], default="text"): 출력 형식
- `--output` / `-o` (Path, optional): 출력 파일

**Output**: 헤더 계층 트리, 섹션 크기 분포, 중복 콘텐츠 리스트

### 3.3. `reallocate` - Chunk Reallocation

**목적**: 유사도 기반으로 chunks를 헤더 아래로 재배치

**Usage**:
```bash
# 기본 reallocation
markdown-reallocator reallocate input.md

# 유사도 임계값 지정
markdown-reallocator reallocate input.md --threshold 0.8

# 출력 파일 지정
markdown-reallocator reallocate input.md -o output.md

# JSON 보고서 출력
markdown-reallocator reallocate input.md --report reallocated_report.json
```

**Arguments**:
- `input_path` (Path | Literal["-"]): 입력 파일 경로 또는 "-" (stdin)

**Options**:
- `--threshold` (float, default=0.7): 재배치 유사도 임계값 (0.0-1.0)
- `--output` / `-o` (Path, default=None): 출력 파일 (기본: stdout)
- `--report` (Path, optional): 재배치 보고서 (JSON)
- `--dry-run` (bool, default=False): 변경 사항만 표시 (실제 수정 안 함)
- `--verbose` / `-v` (bool, default=False): 상세 진행 상황 표시

**Output**:
- Reallocated markdown (stdout 또는 `--output` 파일)
- JSON 보고서 (`--report` 옵션 시):
  ```json
  {
    "summary": {
      "total_chunks": 156,
      "reallocated_chunks": 42,
      "unchanged_chunks": 114
    },
    "reallocations": [
      {
        "chunk_id": "sha256:abc...",
        "original_position": 45,
        "new_position": 23,
        "original_header": "Section A > Subsection 1",
        "new_header": "Section B > Subsection 3",
        "similarity_score": 0.87,
        "reason": "High semantic similarity"
      }
    ]
  }
  ```

### 3.4. `validate` - Result Validation

**목적**: Reallocation 결과 검증 (구조 무결성, 콘텐츠 손실 여부)

**Usage**:
```bash
# 기본 검증
markdown-reallocator validate original.md reallocated.md

# 상세 검증 보고서
markdown-reallocator validate original.md reallocated.md --verbose

# JSON 보고서
markdown-reallocator validate original.md reallocated.md --format json
```

**Arguments**:
- `original_path` (Path): 원본 파일
- `reallocated_path` (Path): Reallocated 파일

**Options**:
- `--format` (Literal["text", "json"], default="text"): 출력 형식
- `--verbose` / `-v` (bool, default=False): 상세 검증 (chunk별 비교)

**Output**:
- ✅ **Pass**: 모든 검증 통과
- ⚠️ **Warning**: 경고 (헤더 구조 변경, 순서 변경 등)
- ❌ **Fail**: 검증 실패 (콘텐츠 손실, 중복 등)

**검증 항목**:
1. Chunk 개수 일치
2. 총 토큰 수 보존
3. 콘텐츠 무결성 (SHA256 해시)
4. 헤더 구조 보존 여부
5. 중복 chunk 여부

## 4. File Structure

```
markdown_reallocator/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py          # Typer app entry point
│   ├── parse_cmd.py     # parse 커맨드 구현
│   ├── analyze_cmd.py   # analyze 커맨드 구현
│   ├── reallocate_cmd.py # reallocate 커맨드 구현
│   ├── validate_cmd.py  # validate 커맨드 구현
│   └── utils.py         # 공통 유틸리티 (Rich 출력, 경로 처리)
├── core/
│   ├── parser.py        # HybridMarkdownParser (기존)
│   ├── splitter.py      # (기존)
│   ├── enrichment.py    # (기존)
│   ├── reallocator.py   # Reallocation 로직
│   └── validator.py     # 검증 로직
└── models/
    ├── chunk.py         # (기존)
    └── report.py        # CLI 보고서 데이터 모델
```

## 5. Implementation Plan

### Phase 1: CLI 기본 구조 (Day 1)
- [x] ~~Typer 설치 및 기본 app 생성~~
- [ ] `main.py` 엔트리포인트 구현
- [ ] `parse` 커맨드 기본 구조
- [ ] Rich 통합 (컬러 출력, 테이블)

### Phase 2: `parse` 커맨드 완성 (Day 1-2)
- [ ] HybridMarkdownParser 통합
- [ ] Text/JSON 출력 형식 구현
- [ ] stdin/stdout 처리
- [ ] 에러 핸들링

### Phase 3: `analyze` 커맨드 (Day 2)
- [ ] 문서 구조 분석 로직
- [ ] 중복 탐지 (유사도 기반)
- [ ] 섹션별 그룹화

### Phase 4: `reallocate` 커맨드 (Day 3-4)
- [ ] Reallocation 알고리즘 구현 (core/reallocator.py)
- [ ] 유사도 계산 (임베딩 기반)
- [ ] Dry-run 모드
- [ ] 진행 상황 표시 (Rich Progress)

### Phase 5: `validate` 커맨드 (Day 4)
- [ ] 검증 로직 구현 (core/validator.py)
- [ ] Chunk 비교 알고리즘
- [ ] 검증 보고서 생성

### Phase 6: 테스트 및 문서화 (Day 5)
- [ ] CLI 통합 테스트 (tests/cli/)
- [ ] 예제 추가 (examples/)
- [ ] README 업데이트
- [ ] pyproject.toml 엔트리포인트 추가

## 6. Code Examples

### 6.1. Main Entry Point (`cli/main.py`)

```python
"""CLI entry point for markdown-reallocator."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console

from markdown_reallocator.cli import (
    parse_cmd,
    analyze_cmd,
    reallocate_cmd,
    validate_cmd,
)

app = typer.Typer(
    name="markdown-reallocator",
    help="Semantic chunking and reallocation for Markdown documents",
    add_completion=False,
)

console = Console()

# Register subcommands
app.command(name="parse")(parse_cmd.parse)
app.command(name="analyze")(analyze_cmd.analyze)
app.command(name="reallocate")(reallocate_cmd.reallocate)
app.command(name="validate")(validate_cmd.validate)


@app.callback()
def callback():
    """
    markdown-reallocator: Semantic chunking and reallocation for Markdown.

    Parse, analyze, and reallocate Markdown documents using semantic chunking.
    """
    pass


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
```

### 6.2. Parse Command (`cli/parse_cmd.py`)

```python
"""Parse command implementation."""

from pathlib import Path
from typing import Literal, Optional
import json
import sys

import typer
from rich.console import Console
from rich.table import Table

from markdown_reallocator.core.parser import HybridMarkdownParser
from markdown_reallocator.models.chunk import MarkdownChunk

console = Console()


def parse(
    input_path: Path = typer.Argument(
        ...,
        help="Input markdown file path or '-' for stdin",
        exists=False,  # Allow "-" for stdin
    ),
    max_tokens: int = typer.Option(
        1024,
        "--max-tokens",
        help="Maximum tokens per chunk",
    ),
    format: Literal["text", "json"] = typer.Option(
        "text",
        "--format",
        help="Output format (text or json)",
    ),
    split_headers: str = typer.Option(
        "h1,h2,h3",
        "--split-headers",
        help="Comma-separated header levels to split on (e.g., 'h1,h2,h3')",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
):
    """Parse markdown file into semantic chunks.

    Examples:

        # Parse file
        $ markdown-reallocator parse input.md

        # Parse from stdin
        $ cat input.md | markdown-reallocator parse -

        # Output JSON
        $ markdown-reallocator parse input.md --format json > chunks.json

        # Custom token limit
        $ markdown-reallocator parse input.md --max-tokens 2000
    """
    try:
        # Read input
        if str(input_path) == "-":
            content = sys.stdin.read()
        else:
            if not input_path.exists():
                console.print(f"[red]Error: File not found: {input_path}[/red]")
                raise typer.Exit(code=1)
            content = input_path.read_text(encoding="utf-8")

        # Parse headers to split on
        headers_to_split = [
            (f"{'#' * int(h[1:])}", h) for h in split_headers.split(",")
        ]

        # Parse markdown
        parser = HybridMarkdownParser(
            max_tokens_per_chunk=max_tokens,
            headers_to_split_on=headers_to_split,
        )
        chunks = parser.parse_text(content)

        # Output
        if format == "json":
            output_json(chunks, output)
        else:
            output_text(chunks, output, max_tokens)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


def output_text(
    chunks: list[MarkdownChunk],
    output_path: Optional[Path],
    max_tokens: int,
):
    """Output chunks in human-readable text format."""
    from io import StringIO

    buffer = StringIO()

    # Summary
    buffer.write("=" * 80 + "\n")
    buffer.write("Document Structure Analysis\n")
    buffer.write("=" * 80 + "\n\n")

    # Statistics
    total_tokens = sum(c.metadata.token_count for c in chunks)
    h1_count = len(set(c.metadata.h1 for c in chunks if c.metadata.h1))
    h2_count = len(set(c.metadata.h2 for c in chunks if c.metadata.h2))
    h3_count = len(set(c.metadata.h3 for c in chunks if c.metadata.h3))

    buffer.write("📊 Summary:\n")
    buffer.write(f"  Total chunks: {len(chunks)}\n")
    buffer.write(f"  Total tokens: {total_tokens:,}\n")
    buffer.write(f"  Headers: h1={h1_count}, h2={h2_count}, h3={h3_count}\n\n")

    # Element type counts
    element_counts = {}
    for chunk in chunks:
        etype = chunk.metadata.element_type.value if chunk.metadata.element_type else "unknown"
        element_counts[etype] = element_counts.get(etype, 0) + 1

    buffer.write("📁 Chunks by Type:\n")
    for etype, count in sorted(element_counts.items(), key=lambda x: -x[1]):
        buffer.write(f"  {etype}: {count}\n")

    # Token statistics
    token_counts = [c.metadata.token_count for c in chunks]
    exceeds = sum(1 for t in token_counts if t > max_tokens)

    buffer.write("\n🔢 Token Statistics:\n")
    buffer.write(f"  Average: {sum(token_counts) / len(token_counts):.1f}\n")
    buffer.write(f"  Min: {min(token_counts)}\n")
    buffer.write(f"  Max: {max(token_counts)}\n")
    if exceeds > 0:
        buffer.write(f"  > {max_tokens} tokens: {exceeds} chunks\n")

    # Warnings
    oversized = [c for c in chunks if c.metadata.token_count > max_tokens]
    if oversized:
        buffer.write("\n⚠️  Warnings:\n")
        for chunk in oversized:
            buffer.write(f"  - Chunk {chunk.metadata.original_position}: {chunk.metadata.token_count} tokens (exceeds limit)\n")

    buffer.write("\n" + "=" * 80 + "\n")
    buffer.write("Chunk Details\n")
    buffer.write("=" * 80 + "\n\n")

    # Chunk details
    for i, chunk in enumerate(chunks[:10], 1):  # First 10 chunks
        buffer.write(f"Chunk {i}:\n")
        buffer.write(f"  ID: {chunk.chunk_id}\n")
        buffer.write(f"  Type: {chunk.metadata.element_type.value if chunk.metadata.element_type else 'unknown'}\n")
        buffer.write(f"  Headers: h1={chunk.metadata.h1}, h2={chunk.metadata.h2}, h3={chunk.metadata.h3}\n")
        buffer.write(f"  Tokens: {chunk.metadata.token_count}\n")
        buffer.write(f"  Content:\n")
        preview = chunk.content[:200].replace("\n", "\n    ")
        buffer.write(f"    {preview}...\n\n")

    if len(chunks) > 10:
        buffer.write(f"... ({len(chunks) - 10} more chunks)\n\n")

    # Write to file or stdout
    result = buffer.getvalue()
    if output_path:
        output_path.write_text(result, encoding="utf-8")
        console.print(f"[green]✓ Output written to {output_path}[/green]")
    else:
        console.print(result)


def output_json(chunks: list[MarkdownChunk], output_path: Optional[Path]):
    """Output chunks in JSON format."""
    # Build summary
    total_tokens = sum(c.metadata.token_count for c in chunks)
    h1_count = len(set(c.metadata.h1 for c in chunks if c.metadata.h1))
    h2_count = len(set(c.metadata.h2 for c in chunks if c.metadata.h2))
    h3_count = len(set(c.metadata.h3 for c in chunks if c.metadata.h3))

    element_counts = {}
    for chunk in chunks:
        etype = chunk.metadata.element_type.value if chunk.metadata.element_type else "unknown"
        element_counts[etype] = element_counts.get(etype, 0) + 1

    token_counts = [c.metadata.token_count for c in chunks]

    data = {
        "summary": {
            "total_chunks": len(chunks),
            "total_tokens": total_tokens,
            "header_counts": {"h1": h1_count, "h2": h2_count, "h3": h3_count},
            "element_counts": element_counts,
            "token_stats": {
                "average": sum(token_counts) / len(token_counts),
                "min": min(token_counts),
                "max": max(token_counts),
            },
        },
        "chunks": [
            {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "metadata": {
                    "h1": chunk.metadata.h1,
                    "h2": chunk.metadata.h2,
                    "h3": chunk.metadata.h3,
                    "element_type": chunk.metadata.element_type.value if chunk.metadata.element_type else None,
                    "token_count": chunk.metadata.token_count,
                    "original_position": chunk.metadata.original_position,
                    "parent_id": chunk.metadata.parent_id,
                    "depth_level": chunk.metadata.depth_level,
                    "sequence_number": chunk.metadata.sequence_number,
                },
            }
            for chunk in chunks
        ],
    }

    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    if output_path:
        output_path.write_text(json_str, encoding="utf-8")
        console.print(f"[green]✓ JSON output written to {output_path}[/green]")
    else:
        console.print(json_str)
```

### 6.3. pyproject.toml Entry Point

```toml
[project.scripts]
markdown-reallocator = "markdown_reallocator.cli.main:main"
```

## 7. Testing Strategy

### Unit Tests (`tests/unit/cli/`)
```python
# tests/unit/cli/test_parse_cmd.py

from typer.testing import CliRunner
from markdown_reallocator.cli.main import app

runner = CliRunner()


def test_parse_basic():
    """Test basic parse command."""
    result = runner.invoke(app, ["parse", "tests/fixtures/simple.md"])
    assert result.exit_code == 0
    assert "Document Structure Analysis" in result.stdout


def test_parse_json_output():
    """Test JSON output format."""
    result = runner.invoke(app, ["parse", "tests/fixtures/simple.md", "--format", "json"])
    assert result.exit_code == 0
    import json
    data = json.loads(result.stdout)
    assert "summary" in data
    assert "chunks" in data


def test_parse_stdin():
    """Test parsing from stdin."""
    result = runner.invoke(app, ["parse", "-"], input="# Test\n\nContent")
    assert result.exit_code == 0
```

### Integration Tests (`tests/integration/`)
```python
# tests/integration/test_cli_workflow.py

def test_parse_analyze_reallocate_workflow(tmp_path):
    """Test full CLI workflow: parse → analyze → reallocate."""
    input_file = tmp_path / "input.md"
    input_file.write_text("# Section 1\n\nContent...\n\n# Section 2\n\nMore content...")

    # Parse
    result = runner.invoke(app, ["parse", str(input_file), "--format", "json", "-o", str(tmp_path / "chunks.json")])
    assert result.exit_code == 0

    # Analyze
    result = runner.invoke(app, ["analyze", str(input_file)])
    assert result.exit_code == 0

    # Reallocate
    output_file = tmp_path / "output.md"
    result = runner.invoke(app, ["reallocate", str(input_file), "-o", str(output_file)])
    assert result.exit_code == 0
    assert output_file.exists()
```

## 8. User Experience Considerations

### Error Messages
- ✅ **명확한 에러 메시지**: "File not found: input.md" (파일 경로 표시)
- ✅ **해결책 제시**: "Try: markdown-reallocator parse --help"
- ✅ **컬러 코딩**: Rich를 사용한 빨강(에러), 노랑(경고), 초록(성공)

### Progress Indicators
```python
from rich.progress import track

for chunk in track(chunks, description="Reallocating chunks..."):
    # Process chunk
    pass
```

### Help Messages
```bash
$ markdown-reallocator parse --help

 Usage: markdown-reallocator parse [OPTIONS] INPUT_PATH

 Parse markdown file into semantic chunks.

╭─ Arguments ─────────────────────────────────────────────────╮
│ *    input_path      PATH  Input markdown file path or '-' │
│                            for stdin [required]             │
╰─────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────╮
│ --max-tokens          INTEGER  Maximum tokens per chunk     │
│                                 [default: 1024]              │
│ --format              TEXT     Output format (text or json) │
│                                 [default: text]              │
│ --output     -o       PATH     Output file path             │
│ --help                         Show this message and exit.  │
╰─────────────────────────────────────────────────────────────╯
```

## 9. Dependencies

### Required (Production)
```toml
[project.dependencies]
typer = "^0.18.0"       # CLI framework
rich = "^13.0.0"        # Terminal formatting
unstructured = "^0.12.0"  # Markdown parsing (기존)
tiktoken = "^0.7.0"     # Token counting (기존)
```

### Development
```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "ruff",
    "mypy",
]
```

## 10. Success Criteria

CLI 구현 완료 시 다음 기준을 만족해야 함:

1. ✅ **기능 완성도**: 4개 커맨드 모두 정상 작동
2. ✅ **타입 안전성**: mypy 100% 통과
3. ✅ **테스트 커버리지**: CLI 모듈 95% 이상
4. ✅ **문서화**: README 및 `--help` 메시지 완비
5. ✅ **사용성**: stdin/stdout 지원, 에러 메시지 명확
6. ✅ **Unix 철학**: 파이프라인 구성 가능

## 11. Future Enhancements (Post-MVP)

- **Interactive Mode**: `markdown-reallocator interactive` (TUI with textual)
- **Plugins**: Custom element type detectors
- **Configuration File**: `.markdown-reallocator.toml` for project settings
- **Watch Mode**: `markdown-reallocator reallocate --watch input.md`
- **Batch Processing**: `markdown-reallocator batch *.md`
- **Diff Viewer**: `markdown-reallocator diff original.md reallocated.md`

---

**Document Version**: 1.0
**Author**: Claude (AI Assistant)
**Last Updated**: 2025-01-15
