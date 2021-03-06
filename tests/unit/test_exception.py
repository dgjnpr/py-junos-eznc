__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
from jnpr.junos.exception import RpcError, CommitError, ConnectError
from jnpr.junos import Device
from lxml import etree


@attr('unit')
class Test_RpcError(unittest.TestCase):

    def test_rpcerror_repr(self):
        rsp = etree.XML('<root><a>test</a></root>')
        obj = RpcError(rsp=rsp)
        self.assertEquals(str, type(obj.__repr__()))
        self.assertEqual(obj.__repr__(), '<root>\n  <a>test</a>\n</root>\n')

    def test_rpcerror_jxml_check(self):
        # this test is intended to hit jxml code
        rsp = etree.XML('<rpc-reply><a>test</a></rpc-reply>')
        obj = CommitError(rsp=rsp)
        self.assertEqual(type(obj.rpc_error), dict)

    def test_ConnectError(self):
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        obj = ConnectError(self.dev)
        self.assertEqual(obj.user, 'rick')
        self.assertEqual(obj.host, '1.1.1.1')
        self.assertEqual(obj.port, 830)
        self.assertEqual(repr(obj), 'ConnectError(1.1.1.1)')
