"""Command-line interface for Markdown Reallocator.

This module provides the main CLI entry point using typer for
command structure and rich for terminal UI.
"""

from pathlib import Path

import typer
from rich.console import Console

from markdown_reallocator import __version__

# Create main app
app = typer.Typer(
    name="markdown-reallocator",
    help="Intelligent markdown document processing toolkit",
    add_completion=False,
)

# Create console for rich output
console = Console()
error_console = Console(stderr=True, style="bold red")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"markdown-reallocator version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose output",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
    profile: bool = typer.Option(
        False,
        "--profile",
        "-p",
        help="Enable performance profiling and show statistics",
    ),
) -> None:
    """Markdown Reallocator - Intelligent markdown document processing."""
    # Set console color mode
    if no_color:
        console.no_color = True
        error_console.no_color = True

    # Set verbosity (store in app context if needed)
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    # Enable profiling if requested
    if profile:
        from markdown_reallocator.utils.profiling import get_monitor
        get_monitor().enable()


@app.command()
def preprocess(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input markdown file",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (default: stdout)",
    ),
    detect_bold_headers: bool = typer.Option(
        True,
        "--detect-bold-headers/--no-detect-bold-headers",
        help="Convert bold lines to headers",
    ),
) -> None:
    """Normalize markdown structure by detecting and fixing formatting issues.

    Converts standalone bold lines to proper headers and fixes common
    LLM-generated markdown issues.
    """
    try:
        import time

        from markdown_reallocator.core.preprocessor import MarkdownPreprocessor
        from markdown_reallocator.utils.profiling import get_monitor

        monitor = get_monitor()

        # Read input
        start = time.perf_counter()
        content = input_file.read_text(encoding="utf-8")
        if monitor.enabled:
            monitor.record_metric("read_input", time.perf_counter() - start)

        # Process
        start = time.perf_counter()
        preprocessor = MarkdownPreprocessor()
        if detect_bold_headers:
            processed = preprocessor.preprocess(content)
        else:
            processed = content
        if monitor.enabled:
            monitor.record_metric("preprocess", time.perf_counter() - start)

        # Write output
        start = time.perf_counter()
        if output:
            output.write_text(processed, encoding="utf-8")
            console.print(f"[green]✓[/green] Processed {input_file} → {output}")
        else:
            console.print(processed, end="")
        if monitor.enabled:
            monitor.record_metric("write_output", time.perf_counter() - start)

        # Print profiling summary if enabled
        if monitor.enabled:
            console.print(monitor.print_summary())

    except Exception as e:
        error_console.print(f"Error preprocessing file: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def split(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input markdown file",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON file with chunks",
    ),
    max_tokens: int = typer.Option(
        1000,
        "--max-tokens",
        help="Maximum tokens per chunk",
    ),
) -> None:
    """Split markdown into semantic chunks by headers.

    Creates chunks that preserve heading hierarchy and semantic structure.
    """
    try:
        import json

        from markdown_reallocator.core.splitter import MarkdownSplitter

        # Read input
        content = input_file.read_text(encoding="utf-8")

        # Split
        with console.status("[bold blue]Splitting document..."):
            splitter = MarkdownSplitter(max_tokens_per_chunk=max_tokens)
            chunks = splitter.split(content)

        # Format output
        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "content": c.content,
                "metadata": {
                    "h1": c.metadata.h1,
                    "h2": c.metadata.h2,
                    "h3": c.metadata.h3,
                    "original_position": c.metadata.original_position,
                },
            }
            for c in chunks
        ]

        # Write output
        if output:
            output.write_text(json.dumps(chunks_data, indent=2, ensure_ascii=False))
            console.print(f"[green]✓[/green] Split into {len(chunks)} chunks → {output}")
        else:
            console.print_json(data=chunks_data)

    except Exception as e:
        error_console.print(f"Error splitting file: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def embed(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input JSON file with chunks (from split command)",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file for embeddings (.npz)",
    ),
    model: str = typer.Option(
        "embeddinggemma",
        "--model",
        help="Ollama embedding model name",
    ),
    use_cache: bool = typer.Option(
        True,
        "--cache/--no-cache",
        help="Enable embedding cache",
    ),
) -> None:
    """Generate embeddings for document chunks.

    Requires Ollama to be running with the specified embedding model.
    """
    try:
        import json

        from rich.progress import Progress, SpinnerColumn, TextColumn

        from markdown_reallocator.core.embedder import Embedder
        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata

        # Load chunks
        chunks_data = json.loads(input_file.read_text())
        chunks = []
        for data in chunks_data:
            chunk = Chunk(
                chunk_id=data["chunk_id"],
                content=data["content"],
                metadata=ChunkMetadata(
                    h1=data["metadata"].get("h1"),
                    h2=data["metadata"].get("h2"),
                    h3=data["metadata"].get("h3"),
                    original_position=data["metadata"]["original_position"],
                ),
            )
            chunks.append(chunk)

        # Embed with progress
        embedder = Embedder(model_name=model, cache_enabled=use_cache)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Embedding {len(chunks)} chunks...",
                total=None,
            )

            def progress_callback(current: int, total: int) -> None:
                progress.update(task, description=f"Embedding {current}/{total} chunks...")

            embedded_chunks = embedder.embed_batch(chunks, progress_callback)

        # Save embeddings
        embedder.save_embeddings(embedded_chunks, str(output))

        console.print(f"[green]✓[/green] Generated embeddings for {len(embedded_chunks)} chunks → {output}")

        # Show cache stats if available
        if use_cache:
            stats = embedder.get_cache_stats()
            if stats:
                console.print(f"  Cache: {stats['hits']} hits, {stats['misses']} misses ({stats['hit_rate']:.1%} hit rate)")

    except Exception as e:
        error_console.print(f"Error generating embeddings: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search query",
    ),
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input JSON file with embedded chunks",
    ),
    embeddings_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Embeddings file (.npz)",
    ),
    top_k: int = typer.Option(
        5,
        "--top-k",
        "-k",
        help="Number of results to return",
    ),
    min_similarity: float = typer.Option(
        0.5,
        "--min-similarity",
        help="Minimum similarity threshold (0.0-1.0)",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format (text or json)",
    ),
) -> None:
    """Search for chunks similar to a query.

    Performs semantic search using embeddings to find relevant chunks.
    """
    try:
        import json

        from markdown_reallocator.core.embedder import Embedder
        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
        from markdown_reallocator.modules.search import SearchModule

        # Load chunks
        chunks_data = json.loads(input_file.read_text())
        chunks = []
        for data in chunks_data:
            chunk = Chunk(
                chunk_id=data["chunk_id"],
                content=data["content"],
                metadata=ChunkMetadata(
                    h1=data["metadata"].get("h1"),
                    h2=data["metadata"].get("h2"),
                    h3=data["metadata"].get("h3"),
                    original_position=data["metadata"]["original_position"],
                ),
            )
            chunks.append(chunk)

        # Load embeddings
        embedder = Embedder()
        embedder.load_embeddings(chunks, str(embeddings_file))

        # Search
        search_module = SearchModule(
            embedder=embedder,
            top_k=top_k,
            min_similarity=min_similarity,
            output_format=output_format,
        )

        results = search_module.search(query, chunks)
        formatted = search_module.format_results(results, include_context=True)

        console.print(formatted)

    except Exception as e:
        error_console.print(f"Error searching: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def reorder(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input JSON file with embedded chunks",
    ),
    embeddings_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Embeddings file (.npz)",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output markdown file",
    ),
    strategy: str = typer.Option(
        "sequential",
        "--strategy",
        "-s",
        help="Reordering strategy (sequential or cluster)",
    ),
) -> None:
    """Reorder chunks by semantic similarity.

    Reorganizes document chunks to improve topical flow and coherence.
    """
    try:
        import json

        from markdown_reallocator.core.embedder import Embedder
        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
        from markdown_reallocator.modules.reorder import ReorderModule

        # Load chunks
        chunks_data = json.loads(input_file.read_text())
        chunks = []
        for data in chunks_data:
            chunk = Chunk(
                chunk_id=data["chunk_id"],
                content=data["content"],
                metadata=ChunkMetadata(
                    h1=data["metadata"].get("h1"),
                    h2=data["metadata"].get("h2"),
                    h3=data["metadata"].get("h3"),
                    original_position=data["metadata"]["original_position"],
                ),
            )
            chunks.append(chunk)

        # Load embeddings
        embedder = Embedder()
        embedder.load_embeddings(chunks, str(embeddings_file))

        # Reorder
        with console.status(f"[bold blue]Reordering with {strategy} strategy..."):
            reorder_module = ReorderModule(strategy=strategy)
            reordered = reorder_module.reorder(chunks)

        # Reconstruct markdown
        markdown = reorder_module.reconstruct_markdown(reordered)

        # Write output
        output.write_text(markdown, encoding="utf-8")
        console.print(f"[green]✓[/green] Reordered {len(chunks)} chunks → {output}")

    except Exception as e:
        error_console.print(f"Error reordering: {e}")
        raise typer.Exit(code=1) from e


@app.command()
def dedup(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Input JSON file with embedded chunks",
    ),
    embeddings_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Embeddings file (.npz)",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output JSON file with deduplicated chunks",
    ),
    similarity_threshold: float = typer.Option(
        0.85,
        "--threshold",
        "-t",
        help="Similarity threshold for duplicates (0.0-1.0)",
    ),
    strategy: str = typer.Option(
        "first",
        "--strategy",
        "-s",
        help="Selection strategy (first, longest, best_metadata)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be removed without actually removing",
    ),
) -> None:
    """Remove duplicate or near-duplicate chunks.

    Identifies and removes redundant chunks based on embedding similarity.
    """
    try:
        import json

        from markdown_reallocator.core.embedder import Embedder
        from markdown_reallocator.models.chunk import Chunk, ChunkMetadata
        from markdown_reallocator.modules.dedup import DeduplicationModule

        # Load chunks
        chunks_data = json.loads(input_file.read_text())
        chunks = []
        for data in chunks_data:
            chunk = Chunk(
                chunk_id=data["chunk_id"],
                content=data["content"],
                metadata=ChunkMetadata(
                    h1=data["metadata"].get("h1"),
                    h2=data["metadata"].get("h2"),
                    h3=data["metadata"].get("h3"),
                    original_position=data["metadata"]["original_position"],
                ),
            )
            chunks.append(chunk)

        # Load embeddings
        embedder = Embedder()
        embedder.load_embeddings(chunks, str(embeddings_file))

        # Deduplicate
        with console.status("[bold blue]Finding duplicates..."):
            dedup_module = DeduplicationModule(
                similarity_threshold=similarity_threshold,
                selection_strategy=strategy,
                dry_run=dry_run,
            )
            deduplicated, report = dedup_module.deduplicate(chunks)

        # Show report
        formatted_report = dedup_module.format_report(report)
        console.print(formatted_report)

        # Save if not dry run
        if not dry_run:
            chunks_data = [
                {
                    "chunk_id": c.chunk_id,
                    "content": c.content,
                    "metadata": {
                        "h1": c.metadata.h1,
                        "h2": c.metadata.h2,
                        "h3": c.metadata.h3,
                        "original_position": c.metadata.original_position,
                    },
                }
                for c in deduplicated
            ]
            output.write_text(json.dumps(chunks_data, indent=2, ensure_ascii=False))
            console.print(f"\n[green]✓[/green] Saved {len(deduplicated)} chunks → {output}")

    except Exception as e:
        error_console.print(f"Error deduplicating: {e}")
        raise typer.Exit(code=1) from e


def cli() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    cli()
