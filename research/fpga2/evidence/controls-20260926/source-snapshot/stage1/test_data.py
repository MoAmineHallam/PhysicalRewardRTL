import json
from pathlib import Path
import tempfile
import unittest
from .prepare_data import records, text_hash


class DataTests(unittest.TestCase):
    def test_truncated_tail_requires_explicit_option(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'input.jsonl'
            p.write_bytes(b'{"text":"ok"}\n{"text":"cut')
            with self.assertRaises(ValueError):
                list(records(p, {}, False))
            audit = {}
            self.assertEqual(list(records(p, audit, True)), ['ok'])
            self.assertEqual(audit['excluded_truncated_tail_line'], 2)
            self.assertEqual(audit['complete_records'], 1)

    def test_middle_corruption_is_fatal_even_with_tail_option(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'input.jsonl'
            p.write_bytes(b'{"text":"ok"}\nBAD\n{"text":"also ok"}\n')
            with self.assertRaises(ValueError):
                list(records(p, {}, True))

    def test_whitespace_duplicate_identity(self):
        self.assertEqual(text_hash('a  b\nc'), text_hash(' a b c '))
        self.assertNotEqual(text_hash('a b'), text_hash('a c'))


if __name__ == '__main__':
    unittest.main()
