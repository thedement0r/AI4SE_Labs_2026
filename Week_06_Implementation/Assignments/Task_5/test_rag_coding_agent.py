"""Unit tests use fictional Example.answer and mocked API responses, not lab solutions."""

import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import sys

import rag_coding_agent as agent

SOURCE = ('# café\r\nclass Example:\r\n    @staticmethod\r\n'
          '    def answer(value: int = 1) -> int:\r\n        pass\r\n\r\n'
          '    def untouched(self):\r\n        return "unchanged"\r\n')
TASK = {'file': 'playground/playground/example.py', 'class': 'Example',
        'method': 'answer', 'description': 'Return the supplied value plus one.'}


def response(code='def answer(value: int = 1) -> int:\n    return value + 1\n', **overrides):
    return json.dumps({**TASK, 'implementation': code, **overrides})


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=agent.HERE, prefix='agent-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        self.path = self.repo / TASK['file']
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(SOURCE.encode('utf-8'))

    def test_actual_task_schema_has_ten_missing_methods(self):
        tasks = agent.load_tasks(agent.ASSIGNMENTS / 'missing_code.json')
        self.assertEqual(len(tasks), 10)
        for task in tasks:
            path = agent.target_path(agent.DEFAULT_REPO, task['file'])
            _, method = agent.find_method(path.read_bytes().decode('utf-8-sig'), task['class'], task['method'])
            self.assertIsInstance(agent.placeholder(method), ast.Pass)

    def test_valid_patch_preserves_crlf_decorator_and_other_source(self):
        original = self.path.read_bytes()
        patched = agent.build_patch(original, TASK, response())
        self.assertIn(b'@staticmethod\r\n', patched)
        self.assertIn(b'        return value + 1\r\n', patched)
        self.assertNotIn(b'\n', patched.replace(b'\r\n', b''))
        self.assertEqual(patched, original.replace(b'        pass', b'        return value + 1'))

    def test_signature_target_and_decorator_changes_rejected(self):
        responses = [response(method='wrong'), response(file='../outside.py'), response(**{'class': 'Other'}),
                     response('def answer(other: int = 1) -> int:\n    return other\n'),
                     response('@staticmethod\ndef answer(value: int = 1) -> int:\n    return value\n'),
                     response('def answer(value: int = 1) -> str:\n    return "x"\n')]
        for candidate in responses:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError):
                    agent.build_patch(self.path.read_bytes(), TASK, candidate)
        self.assertEqual(self.path.read_bytes(), SOURCE.encode('utf-8'))

    def test_invalid_syntax_extra_source_and_placeholders_rejected(self):
        for candidate in ('not JSON', response('def answer(:\n    return 1'),
                          response('import os\ndef answer(value: int = 1) -> int:\n    return value\n'),
                          response('class Other:\n    pass\n'),
                          response('def answer(value: int = 1) -> int:\n    pass\n')):
            with self.subTest(candidate=candidate):
                with self.assertRaises((ValueError, SyntaxError)):
                    agent.build_patch(self.path.read_bytes(), TASK, candidate)

    def test_existing_implementation_cannot_be_overwritten(self):
        raw = SOURCE.replace('        pass', '        return 10').encode('utf-8')
        with self.assertRaises(ValueError):
            agent.build_patch(raw, TASK, response())

    def test_original_docstring_is_preserved(self):
        raw=SOURCE.replace('        pass', '        """Original documentation."""\r\n        pass').encode('utf-8')
        code='def answer(value: int = 1) -> int:\n    """Different documentation."""\n    return value + 1\n'
        patched=agent.build_patch(raw,TASK,response(code))
        self.assertIn(b'Original documentation.',patched)
        self.assertNotIn(b'Different documentation.',patched)

    def test_backup_and_atomic_commit(self):
        raw=self.path.read_bytes()
        patched=agent.build_patch(raw,TASK,response())
        backup=self.root/'backup/example.py'
        agent.commit_patch(self.path,raw,patched,backup)
        self.assertEqual(backup.read_bytes(),raw)
        self.assertEqual(self.path.read_bytes(),patched)
        self.assertFalse(list(self.path.parent.glob('.rag-*.tmp')))

    def test_concurrent_change_rejected_before_writing(self):
        raw=self.path.read_bytes()
        patched=agent.build_patch(raw,TASK,response())
        self.path.write_bytes(raw+b'# concurrent edit\r\n')
        with self.assertRaises(ValueError):
            agent.commit_patch(self.path,raw,patched,self.root/'backup.py')
        self.assertTrue(self.path.read_bytes().endswith(b'# concurrent edit\r\n'))

    def test_outside_paths_tests_and_git_metadata_rejected(self):
        for name in ('../outside.py','playground/tests/test_example.py','.git/config',str(self.root/'outside.py'),
                     str(self.path),'playground/playground/../playground/example.py'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    agent.target_path(self.repo,name)

    def test_scope_audit_detects_unrelated_method_change(self):
        before=agent.project_hashes(self.repo)
        originals={TASK['file']: self.path.read_bytes()}
        self.path.write_bytes(SOURCE.replace('"unchanged"','"changed"').encode('utf-8'))
        with self.assertRaises(ValueError):
            agent.audit_changes(self.repo,originals,before,[{**TASK,'id':'Example.answer'}])

    def test_model_allowlist_and_env_precedence(self):
        path=self.root/'.env'
        path.write_text('OPENAI_MODEL=gpt-5-mini\n',encoding='utf-8')
        with patch.dict('os.environ',{'OPENAI_MODEL':'gpt-4o-mini'},clear=True):
            self.assertEqual(agent.load_configuration(path)['model'],'gpt-4o-mini')
            self.assertFalse(agent.load_configuration(path)['key'])
        with patch.dict('os.environ',{'OPENAI_MODEL':'outside-allowlist'},clear=True):
            with self.assertRaises(ValueError):
                agent.load_configuration(path)
        with self.assertRaises(ValueError):
            agent.AllowedLLM({'model':'outside-allowlist'})

    def test_mocked_sdk_call_and_allowed_fallback(self):
        import httpx
        from openai import NotFoundError
        missing=NotFoundError('fixture: model missing',response=httpx.Response(404,
                              request=httpx.Request('POST','https://example.invalid/v1/chat/completions')),body=None)
        completion=SimpleNamespace(model='gpt-4o-mini',choices=[SimpleNamespace(
            finish_reason='stop',message=SimpleNamespace(content=response()))])
        with patch('openai.OpenAI') as constructor:
            constructor.return_value.chat.completions.create.side_effect=[missing,completion]
            llm=agent.AllowedLLM({'model':'gpt-5-mini','key':'','base_url':None})
            attempts=[]
            text,model=llm.generate('fictional test prompt',attempts)
        self.assertEqual(model,'gpt-4o-mini')
        self.assertEqual(json.loads(text)['method'],'answer')
        self.assertEqual([a['model'] for a in attempts],['gpt-5-mini','gpt-4o-mini'])
        self.assertTrue(all(a['model'] in agent.ALLOWED_MODELS for a in attempts))

    def test_sdk_errors_do_not_expose_transport_details(self):
        configuration={'model':'gpt-5-mini','key':'','base_url':None}
        with patch('openai.OpenAI',side_effect=ValueError('private endpoint detail')):
            with self.assertRaises(ValueError) as captured:
                agent.AllowedLLM(configuration)
        self.assertNotIn('private endpoint detail',str(captured.exception))
        with patch('openai.OpenAI') as constructor:
            constructor.return_value.chat.completions.create.side_effect=RuntimeError('private endpoint detail')
            llm=agent.AllowedLLM(configuration)
            attempts=[]
            with self.assertRaises(RuntimeError) as captured:
                llm.generate('fictional prompt',attempts)
        self.assertNotIn('private endpoint detail',str(captured.exception))
        self.assertNotIn('private endpoint detail',json.dumps(attempts))

    def test_mocked_pipeline_edits_only_fictional_target(self):
        for name in ('Task_3','Task_4'):
            sys.path.insert(0,str(agent.ASSIGNMENTS/name))
        import numpy as np
        storage=json.loads((agent.ASSIGNMENTS/'Task_3/chunk_embeddings.json').read_text(encoding='utf-8'))
        run=self.root/'run'
        run.mkdir()
        coding=agent.RAGCodingAgent.__new__(agent.RAGCodingAgent)
        coding.repo,coding.storage,coding.run_dir=self.repo,storage,run
        coding.model,coding.requested_model,coding.modified=object(),'gpt-5-mini',[]
        coding.llm=SimpleNamespace(generate=lambda prompt,attempts:(response(),'gpt-5-mini'))
        with patch('generate_embeddings.embed_texts',return_value=(np.array([storage['chunks'][0]['embedding']]),
                    [{'token_count':10,'window_count':1,'truncated_tokens':0}])):
            record=coding.solve_task(TASK['description'],TASK['file'],TASK['class'],TASK['method'])
        self.assertEqual(record['status'],'updated',record['error'])
        self.assertEqual(len(record['retrieved_chunks']),5)
        self.assertTrue(record['generation_succeeded'] and record['syntax_valid'] and record['source_modified'])
        self.assertIn(b'return value + 1',self.path.read_bytes())
        self.assertTrue((run/'backups'/TASK['file']).is_file())


if __name__=='__main__':
    unittest.main()
