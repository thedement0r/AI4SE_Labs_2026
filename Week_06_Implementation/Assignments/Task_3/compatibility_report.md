# Task 3 tokenizer compatibility fix

## Cause and changes

The original command was reproduced before editing and failed with `AttributeError: BertTokenizer has no attribute prepare_for_model`. The active `python` uses Sentence Transformers **6.3.0**, Transformers **5.23.0**, torch **2.15.0**, numpy **2.3.4**, and tokenizers **0.23.3**. Its fast `BertTokenizer` also lacks `build_inputs_with_special_tokens`, so merely switching between these two legacy methods would still fail.

`generate_embeddings.py` now uses the tokenizer's normal encoding interface with `return_overflowing_tokens=True`, a 256-token maximum including special tokens, and 32-token stride. The original token-window helper still defines the payload windows and weights. Explicit checks compare every resulting payload token ID and window count with those original windows. No decoding/re-encoding is used; overflow returns every window rather than dropping the tail. Masks are supplied by the tokenizer and only model input fields are passed to the model. See the [Hugging Face tokenizer API](https://huggingface.co/docs/transformers/main_classes/tokenizer).

The loader prefers `get_embedding_dimension()` and falls back to `get_sentence_embedding_dimension()` only when the newer method is unavailable. Regression runs treat FutureWarnings as errors rather than suppressing them.

Further testing found that Transformers 5 also removed the private `BertConfig._commit_hash` attribute. Indexing now records an explicit `MODEL_REVISION` constant, and loading defaults to that same revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. This is the revision already used by the stored dataset. Search continues to request the stored revision explicitly.

`search_chunks.py` was inspected and needed no edits: it imports the same `embed_texts()` and `load_model()` functions used by indexing. Representation construction, weighted window pooling, normalization, 254-token payload capacity, 32-token overlap, 256-token input limit, and 384 dimensions are preserved.

Dependency constraints now admit both tested environments. No package was installed, upgraded, or downgraded during this repair. `pip check` passed in both environments. The old virtual environment still emits a tokenizer padding performance advisory; it is not a FutureWarning or an embedding correctness failure.

## Exact source changes

The diffs below normalize text-file encoding and line endings. New regression tests are in `test_embedding_compatibility.py`; the historical embedding report now links to this update.

```diff
--- before/generate_embeddings.py
+++ after/generate_embeddings.py
@@ -18,11 +18,13 @@
 
 HERE = Path(__file__).resolve().parent
 MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
+# Pin the revision used by the existing storage; no private config API needed.
+MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
 DIMENSIONS = 384
 TOKEN_OVERLAP = 32
 
 
-def load_model(revision=None, offline=False):
+def load_model(revision=MODEL_REVISION, offline=False):
     """Use CPU inference and a cache isolated from the original repository."""
     os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
     torch.set_num_threads(min(4, os.cpu_count() or 1))
@@ -32,7 +34,11 @@
         token=False,
     )
     model.eval()
-    if model.get_sentence_embedding_dimension() != DIMENSIONS:
+    # Sentence Transformers 6 renamed this API; older releases need the fallback.
+    get_dimension = getattr(model, "get_embedding_dimension", None)
+    if get_dimension is None:
+        get_dimension = model.get_sentence_embedding_dimension
+    if get_dimension() != DIMENSIONS:
         raise ValueError("Unexpected model embedding dimension")
     return model
 
@@ -112,7 +118,7 @@
 
 
 def embed_texts(model, texts, overlap=TOKEN_OVERLAP, batch_size=16):
-    """Encode token IDs directly, avoiding decode/re-encode drift and truncation."""
+    """Encode complete text with checked overflow windows and no token loss."""
     tokenizer = model.tokenizer
     capacity = model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False)
     inputs, owners, weights, statistics = [], [], [], []
@@ -122,11 +128,26 @@
             raise ValueError("Cannot embed empty text")
         windows = list(token_windows(ids, capacity, overlap))
         statistics.append({"token_count": len(ids), "window_count": len(windows), "truncated_tokens": 0})
-        for window, weight in windows:
-            item = tokenizer.prepare_for_model(
-                window, add_special_tokens=True, truncation=False,
-                return_attention_mask=True, return_token_type_ids=True,
-            )
+        # The normal tokenizer interface works across Transformers 4 and 5.
+        # Overflow keeps the complete text, even though each individual window
+        # is limited to max_seq_length (including the model's special tokens).
+        encoded = tokenizer(
+            text, add_special_tokens=True, truncation=True,
+            max_length=model.max_seq_length, stride=overlap,
+            return_overflowing_tokens=True, return_special_tokens_mask=True,
+            return_attention_mask=True, return_token_type_ids=True,
+            padding=False, verbose=False,
+        )
+        if len(encoded["input_ids"]) != len(windows):
+            raise ValueError("Tokenizer overflow differs from expected token windows")
+        for index, (window, weight) in enumerate(windows):
+            item = {key: encoded[key][index] for key in tokenizer.model_input_names
+                    if key in encoded}
+            payload = [token for token, special in zip(
+                item["input_ids"], encoded["special_tokens_mask"][index]
+            ) if not special]
+            if payload != window:
+                raise ValueError("Tokenizer changed the expected window token IDs")
             if len(item["input_ids"]) > model.max_seq_length:
                 raise ValueError("Token window exceeds the model limit")
             inputs.append(item)
@@ -202,7 +223,7 @@
         "schema_version": 1, "repository": original.get("repository"),
         "input_sha256": hashlib.sha256(raw).hexdigest(),
         "source_metadata": {key: value for key, value in original.items() if key != "chunks"},
-        "model": {"name": MODEL_NAME, "revision": model[0].auto_model.config._commit_hash,
+        "model": {"name": MODEL_NAME, "revision": MODEL_REVISION,
                   "dimensions": DIMENSIONS, "max_sequence_tokens": model.max_seq_length,
                   "payload_tokens": model.max_seq_length - model.tokenizer.num_special_tokens_to_add(False),
                   "token_overlap": TOKEN_OVERLAP, "normalized": True, "device": "cpu",
--- before/requirements.txt
+++ after/requirements.txt
@@ -1,4 +1,4 @@
-sentence-transformers==5.1.2
-transformers==4.57.6
-torch==2.15.0
-numpy==2.5.4
+sentence-transformers>=5.1.2,<7
+transformers>=4.57.6,<6
+torch>=2.15.0,<3
+numpy>=2.3.4,<3
```

## Actual failing-command retest

Executed from Task_3, exactly as requested:

```powershell
python search_chunks.py "Find the code responsible for calculating order prices"
```

Exit code: **0**. Full source content was printed for all five results. A second run with `--offline --summary-only` produced the same ranking:

| Rank | Cosine score | Repository-relative file and lines |
| --- | ---: | --- |
| 1 | 0.422336 | `playground/playground/orders.py:43?124` |
| 2 | 0.403844 | `playground/playground/orders.py:125?196` |
| 3 | 0.386062 | `playground/playground/__init__.py:1?49` |
| 4 | 0.375270 | `playground/tests/test_orders.py:246?332` |
| 5 | 0.373801 | `playground/tests/test_orders.py:147?245` |

The first result contains `Order.total`, which delegates to the pricing strategy. Rank 2 and rank 4 provide order-construction context; rank 3 is mostly exports. Rank 5 includes `OrderTotalTests` among other tests. These are useful to varying degrees: the direct arithmetic in `pricing.py` is absent from this exact query's top five. The query including ?and discounts? finds `pricing.py` first. This limitation of the existing semantic representation was preserved rather than hidden by changing ranking or regenerating vectors.

## Additional actual retrieval tests

`python -B search_chunks.py --demo --offline --summary-only` exited 0. All four queries retained the same five chunk IDs, order, and scores as the earlier stored retrieval baseline (verified within `1e-6`).

| Query topic | First result | Cosine score |
| --- | --- | ---: |
| Order prices and discounts | `playground/playground/pricing.py:1?68` | 0.442685 |
| Warehouse inventory and reservations | `playground/playground/inventory.py:84?155` | 0.496940 |
| Customer credit limits | `playground/playground/models.py:221?268` | 0.487071 |
| Order status transitions | `playground/playground/orders.py:1?42` | 0.548308 |

The existing [embedding report](embedding_report.md) and [retrieval results](retrieval_results.json) retain the complete twenty-result tables/content and their relevance limitations. Repeated results matched that baseline.

## Regression and storage verification

Commands executed from Task_3:

```powershell
python -B -W error::FutureWarning -m unittest -v test_embedding_compatibility
.\.venv\Scripts\python.exe -B -W error::FutureWarning -m unittest -v test_embedding_compatibility
```

- Active Python (Sentence Transformers 6.3.0 / Transformers 5.23.0): **4 tests passed**, 26.821 seconds.
- Existing virtual environment (Sentence Transformers 5.1.2 / Transformers 4.57.6): **4 tests passed**, 25.593 seconds.
- In both environments all 58 re-embedded vectors matched storage exactly: maximum absolute difference **0.0**. Every representation and token/window statistic also matched. JSON, IDs, metadata, 384 finite dimensions, and unit norms were validated.
- Short-text embeddings matched ordinary normalized `model.encode` within `1e-6`, while a mock made any attempted `prepare_for_model()` call fail.
- A long-input test verified token coverage, overlap, the last window, and model input bounds; retrieval regression checks covered all four questions and all twenty results.
- The full indexing CLI was executed offline with FutureWarnings treated as errors and a temporary output. It generated **58 vectors from 61,559 representation tokens across 300 windows**, with **zero truncated tokens**. Encoding took **15.165 seconds**; measured total was **15.972 seconds**. All chunk records and model settings matched the existing storage exactly. The temporary output was then removed.

The official `chunk_embeddings.json` was **not regenerated or modified**. Its before/after SHA-256 remains `2a3319c8ec4649ddcb959d87b5080ca43daa581a449ed80acaae9d11b61ac978`. Original source hashes and all three Task 2 file hashes remain unchanged; the cloned repository's Git status is clean and `.git` remains intact.
