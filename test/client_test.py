import unittest

from prisma import Prisma

from mock_client.client import MockClient


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.client = MockClient()

    def test_client(self):
        self.assertIsInstance(self.client, MockClient)
        self.assertIsInstance(self.client, Prisma)
