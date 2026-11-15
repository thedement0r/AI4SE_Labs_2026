"""Task 4 regressions; run: python -B -m unittest -v test_match_embeddings."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from match_embeddings import (
    DEFAULT_STORAGE, DIMENSIONS, HERE, load_query_embedding,
    match_embeddings, read_json, task3_helpers,
)


class MatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = read_json(DEFAULT_STORAGE)
        cls.example = read_json(HERE / 'example_query_embedding.json')
        cls.vector = cls.example['embedding']
        cls.expected_id = cls.example['source_chunk_id']

    def test_collection_dimensions_and_finite_values(self):
        self.assertEqual(len(self.dataset['chunks']), 58)
        self.assertTrue(all(len(c['embedding']) == DIMENSIONS for c in self.dataset['chunks']))
        self.assertTrue(np.isfinite([c['embedding'] for c in self.dataset['chunks']]).all())

    def test_top_one_three_five_are_sorted_and_complete(self):
        for top_k in (1, 3, 5):
            with self.subTest(top_k=top_k):
                results = match_embeddings(self.vector, self.dataset, top_k)
                self.assertEqual(len(results), top_k)
                scores = [r['score'] for r in results]
                self.assertEqual(scores, sorted(scores, reverse=True))
                self.assertEqual(results[0]['chunk_id'], self.expected_id)
                self.assertAlmostEqual(scores[0], 1.0, places=12)
                for result in results:
                    self.assertEqual(set(result), {'rank', 'score', 'chunk_id', 'file_path', 'start_line', 'end_line', 'content'})
                    original = next(c for c in self.dataset['chunks'] if c['chunk_id'] == result['chunk_id'])
                    self.assertEqual(result['content'], original['content'])

    def test_more_than_collection_returns_all_sorted_chunks(self):
        results = match_embeddings(self.vector, self.dataset, 100)
        self.assertEqual(len(results), 58)
        self.assertEqual([r['score'] for r in results], sorted((r['score'] for r in results), reverse=True))

    def test_each_of_58_stored_vectors_retrieves_itself_first(self):
        for chunk in self.dataset['chunks']:
            with self.subTest(chunk=chunk['chunk_id']):
                result = match_embeddings(chunk['embedding'], self.dataset, 1)[0]
                self.assertEqual(result['chunk_id'], chunk['chunk_id'])
                self.assertAlmostEqual(result['score'], 1.0, places=12)

    def test_unnormalized_extreme_query_scales_are_safe(self):
        for scale in (10, 1e-300, 1e308):
            result = match_embeddings([value * scale for value in self.vector], self.dataset, 1)[0]
            self.assertEqual(result['chunk_id'], self.expected_id)
            self.assertAlmostEqual(result['score'], 1.0, places=12)

    def test_invalid_dimensions_and_shapes_are_rejected(self):
        for value in ([], [1] * 383, [1] * 385, [[1]] * 384, np.array(1.0), 'not a vector', {}):
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    match_embeddings(value, self.dataset)

    def test_invalid_numeric_values_and_zero_vectors_are_rejected(self):
        for value in (float('nan'), float('inf'), -float('inf'), True, None, '0.1', 10 ** 1000):
            vector = list(self.vector)
            vector[0] = value
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    match_embeddings(vector, self.dataset)
        with self.assertRaises(ValueError):
            match_embeddings([0] * DIMENSIONS, self.dataset)

    def test_invalid_top_k_is_rejected(self):
        for value in (0, -1, 1.5, True, '5', None):
            with self.subTest(top_k=value):
                with self.assertRaises(ValueError):
                    match_embeddings(self.vector, self.dataset, value)

    def test_query_json_formats_and_invalid_json(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix='matching-test-') as directory:
            path = Path(directory) / 'query.json'
            for value in (self.vector, {'embedding': self.vector}):
                path.write_text(json.dumps(value), encoding='utf-8')
                self.assertEqual(load_query_embedding(path), self.vector)
            for text in ('{broken', '{}', 'null', '"text"', '[1, 2]', '[NaN]', '[Infinity]', '[-Infinity]'):
                path.write_text(text, encoding='utf-8')
                with self.subTest(text=text):
                    with self.assertRaises(ValueError):
                        load_query_embedding(path)

    def test_invalid_storage_is_rejected(self):
        for storage in ([], {}, {'model': {}, 'chunks': []}):
            with self.assertRaises(ValueError):
                match_embeddings(self.vector, storage)
        for key, value in (('embedding', [0.1] * 383), ('embedding', [float('nan')] * 384),
                           ('start_line', 0), ('content', None), ('chunk_id', [])):
            data = copy.deepcopy(self.dataset)
            data['chunks'][0][key] = value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    match_embeddings(self.vector, data)
        data = copy.deepcopy(self.dataset)
        data['chunks'][1]['chunk_id'] = data['chunks'][0]['chunk_id']
        with self.assertRaises(ValueError):
            match_embeddings(self.vector, data)

    def test_known_cosines_and_stable_ties(self):
        e0, e1, e2 = np.eye(3, DIMENSIONS)
        vectors = (e0, -e0, e1, e2)
        data = {'model': self.dataset['model'], 'chunks': [
            {'chunk_id': str(i), 'file_path': 'fixture.py', 'start_line': 1,
             'end_line': 1, 'content': 'example', 'embedding': vector.tolist()}
            for i, vector in enumerate(vectors)
        ]}
        results = match_embeddings(e0, data, 4)
        self.assertEqual([r['chunk_id'] for r in results], ['0', '2', '3', '1'])
        self.assertEqual([r['score'] for r in results], [1, 0, 0, -1])

    def test_same_results_as_task3_without_loading_model(self):
        validate_dataset, rank_chunks = task3_helpers()
        expected = rank_chunks(self.dataset['chunks'], validate_dataset(self.dataset), np.asarray(self.vector), 5)
        with patch('generate_embeddings.load_model', side_effect=AssertionError('Model loading is unnecessary')):
            actual = match_embeddings(self.vector, self.dataset, 5)
        self.assertEqual([r['chunk_id'] for r in actual], [r['chunk_id'] for r in expected])
        np.testing.assert_allclose([r['score'] for r in actual], [r['score'] for r in expected], atol=1e-12, rtol=0)

    def test_cli_default_five_and_more_than_collection(self):
        for arguments, count in (([], 5), (['--top-k', '100'], 58)):
            completed = subprocess.run(
                [sys.executable, '-B', str(HERE / 'match_embeddings.py'),
                 str(HERE / 'example_query_embedding.json'), *arguments],
                capture_output=True, text=True, encoding='utf-8', timeout=120,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            results = json.loads(completed.stdout)
            self.assertEqual(len(results), count)
            self.assertEqual(results[0]['chunk_id'], self.expected_id)

    def test_cli_rejects_invalid_input_without_traceback(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix='matching-test-') as directory:
            path = Path(directory) / 'bad.json'
            for text in ('{malformed', '[NaN]', '[Infinity]', '[1, 2]'):
                path.write_text(text, encoding='utf-8')
                completed = subprocess.run(
                    [sys.executable, '-B', str(HERE / 'match_embeddings.py'), str(path)],
                    capture_output=True, text=True, encoding='utf-8', timeout=30,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertIn('error:', completed.stderr)
                self.assertNotIn('Traceback', completed.stderr)


if __name__ == '__main__':
    unittest.main()
