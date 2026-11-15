"""Chunk repository source for RAG using only the Python standard library."""

import argparse
import ast
from bisect import bisect_right
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tokenize


LANGUAGES = {
    **dict.fromkeys((".py", ".pyw", ".pyi"), "python"),
    **dict.fromkeys((".js", ".jsx", ".mjs", ".cjs"), "javascript"),
    **dict.fromkeys((".ts", ".tsx"), "typescript"),
    **dict.fromkeys((".c", ".h"), "c"),
    **dict.fromkeys((".cpp", ".cc", ".cxx", ".hpp", ".hh"), "cpp"),
    ".java": "java", ".cs": "csharp", ".go": "go", ".rs": "rust",
    ".rb": "ruby", ".php": "php", ".swift": "swift", ".kt": "kotlin",
    ".kts": "kotlin", ".scala": "scala", ".sh": "shell", ".bash": "shell",
    ".ps1": "powershell", ".psm1": "powershell", ".sql": "sql",
    ".r": "r", ".lua": "lua", ".html": "html", ".css": "css",
    ".scss": "scss", ".vue": "vue", ".svelte": "svelte",
}
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "venv", ".venv", "env",
    "__pycache__", "__pypackages__", "build", "dist", "target", "out",
    "bin", "obj", "vendor", "generated", "coverage", "htmlcov", ".next",
    ".nuxt", ".cache", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".nox", ".idea", ".vscode", ".eggs", "_build",
}
GENERATED_NAME = re.compile(r"(?:\.min\.|\.bundle\.|\.generated\.|\.g\.cs$|_pb2(?:_grpc)?\.py$)", re.I)
GENERATED_HEADER = re.compile(r"@generated|do not edit|automatically generated|auto-generated", re.I)
# Conservative hints only; arbitrary languages always have a line-window fallback.
SYMBOL_START = re.compile(
    r"^\s*(?:(?:export|default|public|private|protected|static|async|abstract|final)\s+)*"
    r"(?:class|interface|enum|struct|trait|impl|function|def|fn|func|module|namespace)\b"
)


def source_files(root, excluded_dirs):
    """Walk deterministically without following directory or file symlinks."""
    def onerror(error):
        # A partial scan must not look like a successful full scan.
        raise error

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        kept = []
        for name in sorted(dirs):
            path = Path(directory) / name
            if (name.lower() in EXCLUDED_DIRS or name.lower().endswith(".egg-info")
                    or path.is_symlink() or path.is_junction()):
                excluded_dirs.append(path.relative_to(root).as_posix())
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(names):
            yield Path(directory) / name


def decode_source(raw, language):
    """Respect Python coding cookies and common Unicode BOMs; flag replacement."""
    try:
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            encoding = "utf-16"
        elif language == "python":
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
        else:
            encoding = "utf-8-sig"
        return raw.decode(encoding), encoding, None
    except (UnicodeError, SyntaxError, LookupError) as error:
        return raw.decode("utf-8-sig", errors="replace"), "utf-8-sig/replacement", str(error)


def boundary_hints(text, lines, language, limit):
    """Return zero-based cut positions, keeping small Python definitions intact."""
    cuts = {len(lines)}
    if language == "python":
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError):
            return sorted(cuts), "line_windows (Python parse fallback)"

        def visit(nodes):
            for node in nodes:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
                    cuts.update((start, node.end_lineno))
                    if isinstance(node, ast.ClassDef) and node.end_lineno - start > limit:
                        visit(node.body)

        visit(tree.body)
        return sorted(cuts), "python_ast"
    cuts.update(i for i, line in enumerate(lines) if SYMBOL_START.match(line))
    return sorted(cuts), "symbol_hints_and_line_windows"


def chunk_ranges(line_count, cuts, limit, overlap):
    """Prefer a structural cut; overlap by ten lines after a forced cut."""
    start = 0
    while start < line_count:
        ceiling = min(start + limit, line_count)
        cut_index = bisect_right(cuts, ceiling)
        candidate = cuts[cut_index - 1] if cut_index else 0
        structural = candidate > start
        end = candidate if structural else ceiling
        yield start, end, not structural and end < line_count
        if end == line_count:
            break
        start = end if structural else end - overlap


def validate_chunks(lines, chunks, limit, overlap):
    """Check full line coverage, exact text, bounds, and forced-cut overlap."""
    covered = 0
    previous = None
    for chunk in chunks:
        start, end = chunk["start_line"] - 1, chunk["end_line"]
        if not (0 <= start < end <= len(lines) and end - start <= limit):
            raise ValueError("Invalid chunk bounds")
        if start > covered or chunk["content"] != "".join(lines[start:end]):
            raise ValueError("Missing or altered source lines")
        if previous:
            expected = overlap if previous["forced_split_after"] else 0
            if previous["end_line"] - start != expected:
                raise ValueError("Incorrect overlap")
        covered = max(covered, end)
        previous = chunk
    if covered != len(lines):
        raise ValueError("Uncovered source lines")


def build_dataset(root, limit=100, overlap=10, max_file_bytes=10 * 1024 * 1024):
    chunks, files, excluded_dirs = [], [], []
    for path in source_files(root, excluded_dirs):
        relative = path.relative_to(root).as_posix()
        language = LANGUAGES.get(path.suffix.lower())
        record = {"file_path": relative, "language": language}
        files.append(record)
        reason = None
        if path.is_symlink():
            reason = "symlink"
        elif not language:
            reason = "unsupported extension or non-source file"
        elif GENERATED_NAME.search(path.name):
            reason = "generated filename"
        if reason:
            record.update(status="skipped", reason=reason)
            continue
        try:
            # Bounded read: never truncate a source file silently.
            with path.open("rb") as stream:
                raw = stream.read(max_file_bytes + 1)
        except OSError as error:
            record.update(status="skipped", reason=f"read error: {error}")
            continue
        if len(raw) > max_file_bytes:
            record.update(status="skipped", reason="exceeds max_file_bytes")
            continue
        text, encoding, warning = decode_source(raw, language)
        if "\x00" in text:
            record.update(status="skipped", reason="binary content (NUL character)")
            continue
        lines = text.splitlines(keepends=True)
        if GENERATED_HEADER.search("".join(lines[:5])):
            record.update(status="skipped", reason="generated-file header")
            continue
        cuts, method = boundary_hints(text, lines, language, limit)
        file_chunks = []
        for index, (start, end, forced) in enumerate(chunk_ranges(len(lines), cuts, limit, overlap)):
            content = "".join(lines[start:end])
            identity = f"{relative}\0{start + 1}\0{end}\0{content}"
            file_chunks.append({
                "chunk_id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                "file_path": relative, "start_line": start + 1, "end_line": end,
                "content": content, "language": language, "chunk_index": index,
                "line_count": end - start, "method": method,
                "forced_split_after": forced,
                "overlap_with_previous": max(0, file_chunks[-1]["end_line"] - start) if file_chunks else 0,
            })
        validate_chunks(lines, file_chunks, limit, overlap)
        record.update(
            status="empty" if not lines else "processed", encoding=encoding,
            decoding_warning=warning, size_bytes=len(raw), line_count=len(lines),
            sha256=hashlib.sha256(raw).hexdigest(), chunk_count=len(file_chunks), method=method,
        )
        chunks.extend(file_chunks)
    if len({chunk["chunk_id"] for chunk in chunks}) != len(chunks):
        raise ValueError("Duplicate chunk IDs")
    statuses = Counter(record["status"] for record in files)
    summary = {
        "source_files_processed": statuses["processed"] + statuses["empty"],
        "nonempty_source_files": statuses["processed"], "empty_source_files": statuses["empty"],
        "files_skipped": statuses["skipped"], "chunks_generated": len(chunks),
        "source_lines": sum(record.get("line_count", 0) for record in files),
        "chunk_lines_including_overlap": sum(chunk["line_count"] for chunk in chunks),
        "largest_chunk_lines": max((chunk["line_count"] for chunk in chunks), default=0),
        "forced_splits": sum(chunk["forced_split_after"] for chunk in chunks),
        "decoding_warnings": sum(bool(record.get("decoding_warning")) for record in files),
        "verification": "passed: exact content, full selected-file coverage, bounds, overlap, unique IDs",
    }
    return {
        "schema_version": 1, "repository": root.name,
        "config": {"max_lines": limit, "overlap_lines": overlap, "max_file_bytes": max_file_bytes,
                   "line_numbers": "1-based inclusive", "source_extensions": sorted(LANGUAGES),
                   "excluded_directory_names": sorted(EXCLUDED_DIRS)},
        "summary": summary, "excluded_directories": excluded_dirs, "files": files, "chunks": chunks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("repository_chunks.json"))
    parser.add_argument("--max-lines", type=int, default=100)
    parser.add_argument("--overlap", type=int, default=10)
    parser.add_argument("--max-file-bytes", type=int, default=10 * 1024 * 1024)
    args = parser.parse_args()
    if not 0 <= args.overlap < args.max_lines or args.max_file_bytes < 1:
        parser.error("Require 0 <= overlap < max-lines and max-file-bytes > 0")
    root, output = args.repository.resolve(), args.output.resolve()
    if not root.is_dir():
        parser.error("Repository must be an existing directory")
    if output.is_relative_to(root):
        parser.error("Output must be outside the source repository")
    dataset = build_dataset(root, args.max_lines, args.overlap, args.max_file_bytes)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(dataset, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with output.open(encoding="utf-8") as stream:
        saved = json.load(stream)
    if saved != dataset:
        raise ValueError("JSON round-trip verification failed")
    print(json.dumps(saved["summary"], indent=2))
    print(f"Output: {output}")


if __name__ == "__main__":
    main()

