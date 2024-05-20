# coding:utf-8

import unittest

from xarg import commands
from xarg.attribute import __version__

from netter.cmds import main


class test_address(unittest.TestCase):

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

    def test_public_ip_random(self):
        self.assertEqual(main("public-ip".split()), 0)

    def test_public_ip_all(self):
        self.assertEqual(main("public-ip --all".split()), 0)

    def test_public_ip_ident(self):
        self.assertEqual(main("public-ip --ident".split()), 0)

    def test_public_ip_ipify(self):
        self.assertEqual(main("public-ip --ipify".split()), 0)

    def test_public_ip_ipinfo(self):
        self.assertEqual(main("public-ip --ipinfo".split()), 0)
