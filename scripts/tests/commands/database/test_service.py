import unittest

from k8s_cluster.commands.database.service import quote_pg_identifier


class TestQuotePgIdentifier(unittest.TestCase):
    def test_simple_name(self):
        self.assertEqual(quote_pg_identifier("kafka-worker"), '"kafka-worker"')

    def test_escapes_quotes(self):
        self.assertEqual(quote_pg_identifier('foo"bar'), '"foo""bar"')
