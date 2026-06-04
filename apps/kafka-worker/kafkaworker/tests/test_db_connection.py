from django.db import connection
from django.test import TestCase


class DatabaseConnectionTestCase(TestCase):
    def test_database_connection(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            self.assertEqual(cursor.fetchone(), (1,))
