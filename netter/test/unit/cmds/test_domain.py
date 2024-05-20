# coding:utf-8

import unittest

from xarg import commands
from xarg.attribute import __version__

from netter.cmds import main


class test_nameserver(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.cmds = commands()

    def tearDown(self):
        pass

    def test_view(self):
        self.assertEqual(main("nameserver".split()), 0)

    def test_probe(self):
        self.assertEqual(main("nameserver probe 8.8.8.8".split()), 0)

    def test_query_ipv6(self):
        self.assertEqual(
            main("nameserver query -6 example.com 8.8.8.8".split()), 0)

    def test_query_and_ping(self):
        self.assertEqual(
            main("nameserver query --ping example.com 8.8.8.8".split()), 0)
