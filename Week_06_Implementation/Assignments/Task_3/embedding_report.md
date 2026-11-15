# Task 3: local embeddings and semantic retrieval

> Compatibility update: the generation measurements below describe the original environment. The scripts now support both installed library versions using checked tokenizer overflow and a pinned model revision; dependency ranges were widened without installing or downgrading packages. See [the exact changes and current test results](compatibility_report.md).

## Objective and model

Embeddings represent code fragments as numeric vectors so RAG can select relevant context for a natural-language coding question. This task adds embedding generation and retrieval to Task 2's existing 58 chunks; it does not implement an LLM agent.

The selected pretrained model is `sentence-transformers/all-MiniLM-L6-v2`, running locally on CPU without a paid API key. It produces **384-dimensional** vectors and normally truncates inputs beyond **256 wordpieces**. See the [official model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). The downloaded model revision is `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; search loads this same revision. The first run downloads public weights; `--offline` uses the existing cache.

## Representation and long chunks

`generate_embeddings.py` reads only Task 2's `repository_chunks.json`. It reconstructs each file from those chunks in memory and parses Python with `ast` to recover enclosing classes and intersecting function names/docstrings, including when a chunk starts inside a class. No checkout source files are needed for indexing.

Each representation contains the relative path, qualified class/function names with identifier words separated, relevant enclosing/intersecting docstrings, and the full dedented chunk code. No query-specific labels or generated summaries are added. Original chunk content and metadata remain unchanged alongside this separate `embedding_text` and `embedding_symbols` representation. Non-Python or unparsable files retain their path and complete code without AST enrichment.

Representations are tokenized **without truncation** and split into windows of at most **254 payload tokens**, leaving two positions for BERT's special tokens. Adjacent windows overlap by **32 tokens**. Token IDs are sent directly through the SentenceTransformer model, avoiding decode/re-tokenize drift. Each window vector is normalized; vectors are averaged with weights equal to newly covered token counts and the final 384-vector is normalized again. Short questions use the same encoder and pooling. Long questions also use windows.

This reduces a long representation to one vector without dropping any input tokens. It can still blur distinct topics; averaging does not preserve every semantic detail. Token counts, window counts, and zero truncation counts are saved per chunk.

## Storage and retrieval

`chunk_embeddings.json` preserves every original chunk field and the original dataset's non-chunk metadata. It adds vectors, embedding representations, per-chunk window statistics, model/revision/configuration, package versions, the input SHA-256, and execution measurements.

JSON is inspectable and sufficient for 58 vectors, though verbose compared with binary arrays. `search_chunks.py` validates the stored vectors, embeds a question, computes exact cosine similarity `dot(a, b) / (norm(a) * norm(b))`, and sorts all chunks. The default is five results, each with score, path, inclusive line range, and complete original source content. Similarity is not a probability or correctness guarantee. No vector database, LangChain, LangGraph, paid API, or final agent is used.

## Environment, commands, and actual generation

Dependencies were installed in `Task_3/.venv`; model files are cached in `Task_3/.model_cache`. A local `.gitignore` excludes the environment, cache, and bytecode. `requirements.txt` pins the tested direct dependencies: sentence-transformers 5.1.2, transformers 4.57.6, torch 2.15.0, and numpy 2.5.4. Python was 3.12.10; `pip check` reported no broken requirements.

Commands executed from the workspace root included:

```powershell
python -m venv Week_06_Implementation\Assignments\Task_3\.venv
.\Week_06_Implementation\Assignments\Task_3\.venv\Scripts\python.exe -m pip install -r Week_06_Implementation\Assignments\Task_3\requirements.txt
.\Week_06_Implementation\Assignments\Task_3\.venv\Scripts\python.exe -B Week_06_Implementation\Assignments\Task_3\generate_embeddings.py
.\Week_06_Implementation\Assignments\Task_3\.venv\Scripts\python.exe -B Week_06_Implementation\Assignments\Task_3\search_chunks.py --demo --offline --summary-only --save-results Week_06_Implementation\Assignments\Task_3\retrieval_results.json
.\Week_06_Implementation\Assignments\Task_3\.venv\Scripts\python.exe -B Week_06_Implementation\Assignments\Task_3\search_chunks.py "Where are order status transitions defined?" --offline --top-k 1
```

Omit `--summary-only` to display full code for all results. For an individual question, replace `--demo` with a quoted question. `retrieval_results.json` records all four actual queries and their complete top-five source contents.

| Measurement | Actual result |
| --- | ---: |
| Chunks / vectors | 58 / 58 |
| Dimensions per vector | 384 |
| Representation tokens, before overlapping | 61,559 |
| Model windows | 300 |
| Chunks requiring multiple windows | 57 |
| Largest representation | 1,626 tokens |
| Truncated representation tokens | 0 |
| Encoding time | 14.689 seconds |
| Total measured generation time | 28.147 seconds |
| Embedding JSON size | 1,189,608 bytes |

Total generation time includes model loading/download and representation preparation after Python imports; dependency installation and interpreter/import startup are excluded.

## Retrieval results and assessment

All paths below are relative to `AI4SE_Playground`. Scores are actual cosine similarities, rounded to six decimals.

### 1. Find the code responsible for calculating order prices and discounts.

| Rank | Score | File and lines |
| --- | ---: | --- |
| 1 | 0.442685 | `playground/playground/pricing.py:1–68` |
| 2 | 0.391793 | `playground/playground/__init__.py:1–49` |
| 3 | 0.375768 | `playground/playground/orders.py:43–124` |
| 4 | 0.363939 | `playground/tests/test_pricing.py:73–168` |
| 5 | 0.349020 | `playground/playground/orders.py:125–196` |

Rank 1 directly contains `FlatPricing.price` and `BulkDiscountPricing`. Rank 3 contains the `Order.total` caller; rank 4 provides relevant discount tests. Rank 2 is package exports and rank 5 mostly order construction/logging, so these provide weaker context. The discount `price` method currently contains `pass`: locating it does not mean a complete discount implementation exists.

### 2. Where is warehouse inventory and stock reservation handled?

| Rank | Score | File and lines |
| --- | ---: | --- |
| 1 | 0.496940 | `playground/playground/inventory.py:84–155` |
| 2 | 0.394381 | `playground/playground/inventory.py:1–83` |
| 3 | 0.384812 | `playground/playground/__init__.py:1–49` |
| 4 | 0.354732 | `playground/playground/simulation.py:85–182` |
| 5 | 0.347731 | `playground/playground/simulation.py:183–213` |

The first two results directly cover `Warehouse`, `ReservationContext`, and `InventoryLedger.reserve/release/commit`. Rank 3 is only exports. Simulation results provide integration/setup context rather than the core stock-accounting implementation.

### 3. Find the implementation of customer credit limits.

| Rank | Score | File and lines |
| --- | ---: | --- |
| 1 | 0.487071 | `playground/playground/models.py:221–268` |
| 2 | 0.427135 | `playground/tests/test_models.py:403–497` |
| 3 | 0.204929 | `playground/tests/test_orders.py:246–332` |
| 4 | 0.183469 | `playground/tests/test_simulation.py:100–187` |
| 5 | 0.179757 | `playground/playground/orders.py:125–196` |

Rank 1 is the `Customer` class, including credit-limit/balance fields and `charge`; rank 2 tests the credit-limit behavior. Ranks 3–5 contain customer/order usage and are weak matches for implementing credit checks. `Customer.can_afford` is still `pass`, so the existing implementation is incomplete. Returning five results therefore does not imply five useful answers.

### 4. Where are order status transitions defined?

| Rank | Score | File and lines |
| --- | ---: | --- |
| 1 | 0.548308 | `playground/playground/orders.py:1–42` |
| 2 | 0.440533 | `playground/tests/test_orders.py:1–74` |
| 3 | 0.317022 | `playground/playground/orders.py:43–124` |
| 4 | 0.290226 | `playground/tests/test_orders.py:333–413` |
| 5 | 0.281953 | `playground/tests/test_orders.py:147–245` |

Rank 1 directly defines `OrderStateMachine.TRANSITIONS` and its accessors. Rank 2 contains state-machine tests; rank 3 contains `Order.advance`; rank 5 includes advance tests. Rank 4 is mainly order-log/status-filter tests and is less direct. The transition table exists, but `OrderStateMachine.transition` itself remains `pass`.

Manual inspection found the primary source location in the first result for all four questions. These four selected examples are a small qualitative check, not a general retrieval benchmark; lower ranks include weak matches.

