from unittest import TestCase


class UnitTest(TestCase):
    def test_sub(self):
        self.assertEqual(1 - 1, 0)

    def test_add(self):
        self.assertEqual(1 + 1, 2)

    def test_mul(self):
        self.assertEqual(1 * 1, 1)
