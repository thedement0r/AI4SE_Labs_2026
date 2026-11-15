# Task 4: matching input embeddings to repository chunks

## Objective and reuse

Given a query embedding, retrieve the top n source chunks from Task 3's existing `chunk_embeddings.json`. The collection contains **58 vectors of 384 dimensions**. No source code, chunks, or embeddings are regenerated.

`match_embeddings.py` reuses Task 3's `validate_dataset()` and `rank_chunks()` helpers without modifying them. It adds strict JSON/query validation and a reusable interface:

```python
from match_embeddings import match_embeddings
results = match_embeddings(query_vector, top_k=3)
```

The optional `storage` argument accepts a JSON path or an already-loaded dataset dictionary, allowing a future agent to avoid repeatedly reading the file. Results contain `rank`, `score` (cosine similarity), `chunk_id`, `file_path`, 1-based inclusive `start_line`/`end_line`, and full original `content`.

## Design decisions

Cosine similarity compares vector direction: `dot(query, chunk) / (norm(query) * norm(chunk))`. Task 3 computes all scores and sorts them descending, retaining storage order for exact ties. The default `--top-k` is 5; any positive integer is accepted. Requests exceeding the collection size return every available chunk without duplication or padding.

Queries need not be unit length. They are normalized after division by their largest absolute component, avoiding overflow/underflow for finite very large/small inputs. Zero vectors are rejected because their cosine is undefined. Validation also rejects wrong dimensions, nested arrays, booleans, strings, nulls, NaN, Infinity, malformed JSON, invalid top-k values, and malformed storage metadata/vectors.

JSON input may be a bare 384-number array or an object with an `embedding` array. Standard output is a JSON array containing the complete ranked results. Invalid CLI input produces an argparse error and exit code 2, rather than a traceback. Storage/query paths resolve independently of the script's location; the default storage path is anchored to the script directory.

The implementation uses existing Task 3 dependencies, with no new installations, vector database, LangChain, or API. Importing the shared helpers imports their Python libraries, but no embedding model weights are loaded, no network access is needed, and no embedding inference runs. Natural-language queries remain supported by Task 3; Task 4 specifically matches already-generated vectors.

## Commands and actual results

Executed from `Week_06_Implementation/Assignments/Task_4`:

```powershell
python -B match_embeddings.py example_query_embedding.json --top-k 5
python -B -m unittest -v test_match_embeddings
```

`example_query_embedding.json` copies the existing `pricing.py:1–68` vector, with source chunk ID `843e09d1aa8676c999774153067441bebb3f4c099d86fab152138b07a4b5f35e`. The CLI exited 0 and emitted five results, including complete source content:

| Rank | Cosine similarity | Repository-relative source |
| --- | ---: | --- |
| 1 | 1.000000000000 | `playground/playground/pricing.py:1–68` |
| 2 | 0.814107681034 | `playground/tests/test_pricing.py:73–168` |
| 3 | 0.768472332099 | `playground/tests/test_pricing.py:1–72` |
| 4 | 0.658328269019 | `playground/playground/simulation.py:1–84` |
| 5 | 0.638016355920 | `playground/playground/models.py:1–93` |

**14 tests passed in 30.124 seconds.** They verified:

- The existing collection has 58 embeddings, each with 384 finite dimensions.
- Top-1, Top-3, and Top-5 return exactly 1, 3, and 5 results, with descending scores and complete result fields/content.
- Requesting 100 returns all 58 results, both through the function and the CLI.
- Every one of the 58 stored vectors retrieves its own chunk first, with cosine similarity 1.0 within 12 decimal places.
- Known identical, orthogonal, and opposite vectors produce scores 1, 0, and -1; tied results preserve input order.
- Invalid dimensions, shapes, numeric types, NaN, positive/negative Infinity, zero vectors, top-k values, malformed JSON/storage, and duplicate stored IDs are rejected.
- Both JSON input formats work. Invalid-input CLI tests exit 2 with no traceback; default CLI retrieval returns five results.
- Unnormalized queries, including scales `1e-300` and `1e308`, retrieve the same first result safely.
- Results match Task 3's ranking and scores within `1e-12`, without calling its model loader.

SHA-256 comparisons confirmed that all **14 Task 2/3 project files** were unchanged, with no additions or removals (runtime environments, model caches, and bytecode were excluded from this inventory). All 27 cloned source-file hashes still match Task 2's inventory. The cloned repository remains clean, and its `.git` directory is intact. Temporary test inputs were confined to Task 4 and removed automatically.

## Advantages and limitations

Reusing the tested ranking code keeps both assignments consistent. JSON input/output and an importable function provide a simple interface for a future agent. Exact search is transparent and suitable for 58 chunks; its cost is approximately `O(N*d + N*log(N))`, including scoring and sorting.

The shared Task 3 module imports add startup time and retain its dependency requirements. Reading/validating the collection on each call is sufficient here; a larger service could cache validated matrices. Queries must use the same model and representation as Task 3: dimensions alone cannot establish compatibility. Self-matching and cosine checks verify the matching mechanism, not general semantic retrieval quality. Similarity scores are not probabilities of relevance.
