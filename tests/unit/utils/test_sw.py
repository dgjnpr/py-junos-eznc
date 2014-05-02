__author__ = "Nitin Kumar, Rick Sherman"
__credits__ = "Jeremy Schulman"

import unittest
from nose.plugins.attrib import attr
import os

from jnpr.junos import Device
from jnpr.junos.exception import RpcError
from jnpr.junos.utils.sw import SW
from jnpr.junos.facts.swver import version_info
from ncclient.manager import Manager, make_device_handler
from ncclient.transport import SSHSession

from mock import patch, MagicMock, call

facts = {'domain': None, 'hostname': 'firefly', 'ifd_style': 'CLASSIC',
         'version_info': version_info('12.1X46-D15.3'),
         '2RE': False, 'serialnumber': 'aaf5fe5f9b88', 'fqdn': 'firefly',
         'virtual': True, 'switch_style': 'NONE', 'version': '12.1X46-D15.3',
         'HOME': '/cf/var/home/rick', 'srx_cluster': False,
         'model': 'FIREFLY-PERIMETER',
         'RE0': {'status': 'Testing',
                 'last_reboot_reason': 'Router rebooted after a '
                 'normal shutdown.',
                 'model': 'FIREFLY-PERIMETER RE',
                 'up_time': '6 hours, 29 minutes, 30 seconds'},
         'vc_capable': False, 'personality': 'SRX_BRANCH'}


@attr('unit')
class TestSW(unittest.TestCase):

    @patch('ncclient.manager.connect')
    def setUp(self, mock_connect):
        mock_connect.side_effect = self._mock_manager
        self.dev = Device(host='1.1.1.1', user='rick', password='password123',
                          gather_facts=False)
        self.dev.open()
        self.sw = self.get_sw()

    @patch('jnpr.junos.Device.execute')
    def get_sw(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.facts_refresh()
        return SW(self.dev)

    @patch('ncclient.operations.session.CloseSession.request')
    def tearDown(self, mock_session):
        self.dev.close()

    @patch('jnpr.junos.Device.execute')
    def test_sw_constructor(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.dev.facts_refresh()
        self.sw = SW(self.dev)
        self.assertFalse(self.sw._multi_RE)
        self.assertFalse(self.sw._multi_MX)
        self.assertFalse(self.sw._multi_VC)

    @patch('__builtin__.open')
    def test_sw_local_sha256(self, mock_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_sha256(package),
                         'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934'
                         'ca495991b7852b855')

    @patch('__builtin__.open')
    def test_sw_local_md5(self, mock_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_md5(package),
                         'd41d8cd98f00b204e9800998ecf8427e')

    @patch('__builtin__.open')
    def test_sw_local_sha1(self, mock_open):
        package = 'test.tgz'
        self.assertEqual(SW.local_sha1(package),
                         'da39a3ee5e6b4b0d3255bfef95601890afd80709')

    @patch('jnpr.junos.utils.sw.SCP')
    def test_sw_put(self, mock_scp):
        package = 'test.tgz'
        self.sw.put(package)
        self.assertIn(call().__enter__().put('test.tgz', '/var/tmp'),
                      mock_scp.mock_calls)

    @patch('jnpr.junos.Device.execute')
    def test_sw_pkgadd(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'test.tgz'
        self.assertTrue(self.sw.pkgadd(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_validate(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'package.tgz'
        self.assertTrue(self.sw.validate(package))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock()

        def myprogress(dev, report):
            pass
        self.assertTrue(self.sw.safe_copy(package, progress=myprogress,
                                          cleanfs=True,
                                          checksum=
                                          '96a35ab371e1ca10408c3caecdbd8a67'))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy_return_false(self, mock_execute):
        # not passing checksum value, will get random from magicmock
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock()

        def myprogress(dev, report):
            pass
        self.assertFalse(self.sw.safe_copy(package, progress=myprogress,
                                           cleanfs=True))
        SW.local_md5.assert_called_with(package)

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_copy_checksum_none(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'safecopy.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock(return_value=
                                 '96a35ab371e1ca10408c3caecdbd8a67')

        def myprogress(dev, report):
            pass
        self.assertTrue(self.sw.safe_copy(package, progress=myprogress,
                                          cleanfs=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_safe_install(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        package = 'install.tgz'
        self.sw.put = MagicMock()
        SW.local_md5 = MagicMock(return_value=
                                 '96a35ab371e1ca10408c3caecdbd8a67')

        def myprogress(dev, report):
            pass
        self.assertTrue(self.sw.install(package, progress=myprogress,
                                        cleanfs=True))

    @patch('jnpr.junos.Device.execute')
    def test_sw_rollback(self, mock_execute):
        # we need proper xml for this test case, update request-package-roll
        # back.xml
        mock_execute.side_effect = self._mock_manager
        self.assertEqual(self.sw.rollback(), '')

    def test_sw_inventory(self):
        self.sw.dev.rpc.file_list = \
            MagicMock(side_effect=self._mock_manager)
        self.assertDictEqual(self.sw.inventory,
                             {'current': None, 'rollback': None})

    @patch('jnpr.junos.Device.execute')
    def test_sw_reboot(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_MX = True
        self.assertIn('Shutdown NOW', self.sw.reboot())

    @patch('jnpr.junos.Device.execute')
    def test_sw_poweroff(self, mock_execute):
        mock_execute.side_effect = self._mock_manager
        self.sw._multi_MX = True
        self.assertIn('Shutdown NOW', self.sw.poweroff())

    def _read_file(self, fname):
        from ncclient.xml_ import NCElement

        fpath = os.path.join(os.path.dirname(__file__),
                             'rpc-reply', fname)
        foo = open(fpath).read()
        if (fname == 'get-rpc-error.xml' or
                fname == 'get-index-error.xml' or
                fname == 'get-system-core-dumps.xml'):
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())
        elif (fname == 'show-configuration.xml' or
              fname == 'show-system-alarms.xml'):
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())._NCElement__doc
        else:
            rpc_reply = NCElement(foo, self.dev._conn._device_handler
                                  .transform_reply())._NCElement__doc[0]
        return rpc_reply

    def _mock_manager(self, *args, **kwargs):
        if kwargs:
            if 'path' in kwargs:
                if kwargs['path'] == '/packages':
                    return self._read_file('file-list_dir.xml')
            device_params = kwargs['device_params']
            device_handler = make_device_handler(device_params)
            session = SSHSession(device_handler)
            return Manager(session, device_handler)

        elif args:
            # print args[0].tag, args[0].text
            if args[0].tag == 'command':
                if args[0].text == 'show cli directory':
                    return self._read_file('show-cli-directory.xml')
                elif args[0].text == 'show configuration':
                    return self._read_file('show-configuration.xml')
                elif args[0].text == 'show system alarms':
                    return self._read_file('show-system-alarms.xml')
                elif args[0].text == 'show system uptime | display xml rpc':
                    return self._read_file('show-system-uptime-rpc.xml')
                else:
                    raise RpcError

            else:
                # print args[0].tag
                return self._read_file(args[0].tag + '.xml')