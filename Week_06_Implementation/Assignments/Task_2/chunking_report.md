# Repository chunking for RAG

## Objective and scope

Split the existing `AI4SE_Playground` checkout into searchable source fragments so a future RAG system can supply relevant code to a coding assistant. This step creates chunks only: no embeddings, vector database, retrieval, or LLM agent. All three deliverables are in this assignment folder, outside the source repository. The checkout and its `.git` directory were preserved.

## Design

`chunk_repository.py` uses only Python's standard library (tested with Python 3.12.10). It scans recursively in sorted order and includes application code and tests. An explicit extension map supports Python, JavaScript/TypeScript, C/C++, Java, C#, Go, Rust, Ruby, shell scripts, SQL, and other common source formats.

The maximum chunk size is **100 lines**. This gives a moderate amount of local code context without making each chunk excessively large. Python's `ast` module identifies definition starts (including decorators) and ends. Small functions/classes remain together; classes larger than the limit expose method boundaries as additional cut positions. Chunks greedily combine adjacent spans up to the limit. Imports, comments, blank lines, and module-level statements are retained. Other languages use conservative declaration hints with a line-window fallback; they do not require language parsers.

When no suitable boundary fits, the chunker uses a 100-line window and starts the next window **10 lines before the previous end**. Thus a 245-line unsplittable block produces inclusive ranges `1–100`, `91–190`, and `181–245`. Overlap is applied after forced splits; structural boundaries do not duplicate lines. None of the actual checkout's blocks required a forced split.

Git metadata, dependencies, virtual environments, caches, build/output directories, directory links, generated filename/header patterns, binary content, and non-source extensions are excluded. Every encountered file outside pruned directories has an inventory entry; skipped files have a reason. UTF-8, Python encoding declarations, and UTF-16 BOMs are supported. Decoding failures use replacement text and record a warning. Empty files are recorded with zero chunks. Reads are bounded by a configurable 10 MiB per-file limit; oversized files are explicitly skipped, never silently truncated.

## Output metadata

`repository_chunks.json` contains `config`, `summary`, `excluded_directories`, `files`, and `chunks`. Each chunk has a deterministic full SHA-256 `chunk_id` derived from its relative path, line range, and content; a slash-separated relative `file_path`; **1-based inclusive** `start_line` and `end_line`; exact decoded `content`; language; zero-based chunk index; line count; method; actual preceding overlap; and a forced-split flag. File records preserve raw-byte SHA-256 hashes, encoding, size, line count, and chunk count. This allows later retrieval results to point back to their source and detect stale files.

## Execution and measured results

Run from the workspace root:

```powershell
python -B Week_06_Implementation\Assignments\Task_2\chunk_repository.py AI4SE_Playground
```

The default output is beside the script. Optional arguments are `--output`, `--max-lines`, `--overlap`, and `--max-file-bytes`. Output inside the source repository is rejected.

| Measurement | Actual result |
| --- | ---: |
| Source files processed, including empty files | 27 |
| Nonempty / empty source files | 26 / 1 |
| Application files / chunks | 13 / 21 |
| Test files / chunks | 14 / 37 |
| Total chunks | 58 |
| Source lines covered | 4,376 |
| Chunk lines including overlap | 4,376 |
| Largest chunk | 99 lines |
| Forced splits / decoding warnings | 0 / 0 |
| JSON size | 210,788 bytes |

The only skipped file was `.gitignore` (non-source); `.git` was pruned. `playground/tests/__init__.py` was empty and is represented in the file inventory without an artificial chunk. No selected source file was skipped.

Verification passed:

- JSON was written, reloaded with `json.load`, and compared with the in-memory dataset.
- An independent audit used `git -C AI4SE_Playground ls-files -- '*.py'` to confirm that all 27 tracked Python files appear in the inventory.
- Each file's raw-byte hash matched. Every source line was covered; chunk content matched the exact indicated source slice, and IDs were unique. All 58 chunks respected the 100-line limit.
- Temporary fixtures passed checks for 100/10 forced splitting of both a long Python function and JavaScript, Python syntax-error fallback, empty files, malformed bytes, a Latin-1 coding declaration, UTF-16, a configurable size cap, binary/generated files, excluded directories, and deterministic output. Fixtures were outside the checkout.
- `git -C AI4SE_Playground status --porcelain` and `git -C AI4SE_Playground diff --exit-code` confirmed the source checkout remained clean; its `.git` directory still exists.

## Examples

These are actual chunks; IDs are abbreviated here only:

| ID prefix | Relative file path | Lines | Method |
| --- | --- | --- | --- |
| `009edb5f72ec` | `playground/playground/models.py` | 1–93 | `python_ast` |
| `206189a801e7` | `playground/playground/orders.py` | 1–42 | `python_ast` |
| `38990d3a3d8d` | `playground/tests/test_base.py` | 1–77 | `python_ast` |

The `orders.py` chunk begins with this source excerpt (the JSON contains the complete 42-line content):

```python
"""Order state-machine, order aggregates, builder, and log."""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterator, List, Tuple
```