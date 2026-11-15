"""Offline compatibility regressions for both installed Transformers environments.

Run from Task_3: python -B -m unittest -v test_embedding_compatibility
"""

import json
import unittest
from unittest.mock import patch
import warnings

import numpy as np

from generate_embeddings import (
    DIMENSIONS, HERE, MODEL_REVISION, embed_texts, load_model, represent_chunk,
    symbols_by_file, token_windows, validate_dataset,
)
from search_chunks import DEMO_QUERIES, rank_chunks


class EmbeddingCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE / 'chunk_embeddings.json').read_text(encoding='utf-8'))
        cls.source = json.loads((HERE.parent / 'Task_2/repository_chunks.json').read_text(encoding='utf-8'))
        with warnings.catch_warnings():
            warnings.simplefilter('error', FutureWarning)
            cls.model = load_model(revision=cls.data['model']['revision'], offline=True)
        cls.matrix = validate_dataset(cls.data, cls.source['chunks'])

    def test_all_stored_embeddings_and_representations_are_unchanged(self):
        chunks = self.data['chunks']
        symbols = symbols_by_file(self.source['chunks'])
        for chunk in chunks:
            text, names = represent_chunk(chunk, symbols[chunk['file_path']])
            self.assertEqual(text, chunk['embedding_text'])
            self.assertEqual(names, chunk['embedding_symbols'])
        vectors, stats = embed_texts(self.model, [c['embedding_text'] for c in chunks])
        self.assertEqual(vectors.shape, (58, DIMENSIONS))
        self.assertTrue(np.isfinite(vectors).all())
        np.testing.assert_allclose(vectors, self.matrix, atol=1e-6, rtol=0)
        self.assertEqual(stats, [c['embedding_metadata'] for c in chunks])
        print(f'\nAll 58 embeddings: maximum absolute difference = {np.max(np.abs(vectors - self.matrix)):.12g}')

    def test_short_input_matches_standard_model_encoder_without_legacy_api(self):
        text = 'Customer credit limit and account balance.'
        with patch.object(self.model.tokenizer, 'prepare_for_model', create=True,
                          side_effect=AssertionError('Unsupported legacy API called')):
            vectors, stats = embed_texts(self.model, [text])
        expected = self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)
        np.testing.assert_allclose(vectors, expected, atol=1e-6, rtol=0)
        self.assertEqual(stats[0]['window_count'], 1)

    def test_long_input_keeps_token_overlap_and_last_window(self):
        text = 'Reserve warehouse inventory for customer orders. ' * 100
        ids = self.model.tokenizer.encode(text, add_special_tokens=False, verbose=False)
        capacity = self.data['model']['payload_tokens']
        overlap = self.data['model']['token_overlap']
        windows = list(token_windows(ids, capacity, overlap))
        self.assertGreater(len(windows), 1)
        rebuilt = windows[0][0] + [token for window, _ in windows[1:] for token in window[overlap:]]
        self.assertEqual(rebuilt, ids)
        self.assertEqual(sum(weight for _, weight in windows), len(ids))
        for previous, following in zip(windows, windows[1:]):
            self.assertEqual(previous[0][-overlap:], following[0][:overlap])
        vectors, stats = embed_texts(self.model, [text])
        self.assertEqual(stats, [{'token_count': len(ids), 'window_count': len(windows), 'truncated_tokens': 0}])
        self.assertEqual(vectors.shape, (1, DIMENSIONS))
        self.assertTrue(np.isfinite(vectors).all())
        self.assertTrue(all(len(window) + 2 <= 256 for window, _ in windows))

    def test_retrieval_and_model_metadata_compatibility(self):
        self.assertEqual(self.model.max_seq_length, 256)
        self.assertEqual(self.model.tokenizer.num_special_tokens_to_add(pair=False), 2)
        self.assertEqual(MODEL_REVISION, self.data['model']['revision'])
        vectors, _ = embed_texts(self.model, DEMO_QUERIES)
        expected = [
            ('playground/playground/pricing.py', 1),
            ('playground/playground/inventory.py', 84),
            ('playground/playground/models.py', 221),
            ('playground/playground/orders.py', 1),
        ]
        baseline = json.loads((HERE / 'retrieval_results.json').read_text(encoding='utf-8'))
        for query, vector, location, old in zip(DEMO_QUERIES, vectors, expected, baseline['searches']):
            results = rank_chunks(self.data['chunks'], self.matrix, vector)
            self.assertEqual(len(results), 5)
            self.assertEqual((results[0]['file_path'], results[0]['start_line']), location)
            self.assertEqual([r['chunk_id'] for r in results], [r['chunk_id'] for r in old['results']])
            np.testing.assert_allclose([r['score'] for r in results],
                                       [r['score'] for r in old['results']], atol=1e-6, rtol=0)


if __name__ == '__main__':
    unittest.main()
