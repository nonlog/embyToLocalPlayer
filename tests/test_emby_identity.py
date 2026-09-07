import configparser
import unittest

from utils.configs import configs
from utils.emby_api import EmbyApi
from utils.emby_api_thin import EmbyApiThin
from utils.emby_identity import (build_emby_authorization, identity_headers, identity_params,
                                 resolve_emby_identity)
from utils import net_tools


class EmbyIdentityTests(unittest.TestCase):
    def config(self, **values):
        cfg = configparser.ConfigParser()
        defaults = {
            'enable': 'yes',
            'enable_host': 'emby.example',
            'device_id': 'spoof-device-id',
            'device_name': 'Pixel 10 Pro',
            'client': 'Emby for Android',
            'version': '3.4.16',
            'user_agent': 'Mozilla/5.0 TestAndroid',
        }
        defaults.update(values)
        cfg.read_dict({'emby_identity': defaults})
        return cfg

    def test_disabled_identity_is_inert(self):
        cfg = self.config(enable='no')
        identity = resolve_emby_identity(
            netloc='emby.example', device_id='incoming-id', client='embyToLocalPlayer',
            user_agent='embyToLocalPlayer/1.1', config=cfg)
        self.assertFalse(identity['enabled'])
        self.assertEqual(identity['device_id'], 'incoming-id')
        self.assertEqual(identity['client'], 'embyToLocalPlayer')
        self.assertEqual(identity_params(identity, token='secret'), {})
        self.assertEqual(identity_headers(identity, token='secret', base={'A': 'B'}), {'A': 'B'})

    def test_enabled_identity_maps_to_emby_headers_query_and_authorization(self):
        identity = resolve_emby_identity(netloc='emby.example', device_id='incoming-id', config=self.config())
        self.assertTrue(identity['enabled'])
        self.assertEqual(identity['device_id'], 'spoof-device-id')
        params = identity_params(identity, token='secret')
        self.assertEqual(params['X-Emby-Client'], 'Emby for Android')
        self.assertEqual(params['X-Emby-Device-Name'], 'Pixel 10 Pro')
        self.assertEqual(params['X-Emby-Device-Id'], 'spoof-device-id')
        self.assertEqual(params['X-Emby-Client-Version'], '3.4.16')
        self.assertEqual(params['X-Emby-Token'], 'secret')
        headers = identity_headers(identity, token='secret')
        self.assertEqual(headers['User-Agent'], 'Mozilla/5.0 TestAndroid')
        auth = build_emby_authorization('secret', identity)
        self.assertIn('Client="Emby for Android"', auth)
        self.assertIn('Device="Pixel 10 Pro"', auth)
        self.assertIn('DeviceId="spoof-device-id"', auth)
        self.assertIn('Version="3.4.16"', auth)
        self.assertIn('Token="secret"', auth)
        self.assertEqual(headers['X-Emby-Authorization'], auth)

    def test_host_filter_prevents_spoofing_other_servers(self):
        identity = resolve_emby_identity(netloc='jellyfin.example', device_id='incoming-id', config=self.config())
        self.assertFalse(identity['enabled'])
        self.assertEqual(identity['device_id'], 'incoming-id')

    def test_dot_host_filter_means_all_hosts(self):
        identity = resolve_emby_identity(
            netloc='localhost', device_id='incoming-id', config=self.config(enable_host='.'))
        self.assertTrue(identity['enabled'])
        self.assertEqual(identity['device_id'], 'spoof-device-id')

    def test_playback_progress_requests_use_configured_identity(self):
        original_config = configs.raw
        original_request = net_tools.requests_urllib
        calls = []
        try:
            configs.raw = self.config()
            net_tools.requests_urllib = lambda host, **kwargs: calls.append((host, kwargs))
            net_tools.change_emby_play_position(
                scheme='https', netloc='emby.example', item_id='1', api_key='secret',
                stop_sec=42, play_session_id='session', device_id='incoming-id')
            self.assertEqual(len(calls), 2)
            for _, kwargs in calls:
                self.assertEqual(kwargs['params']['X-Emby-Device-Id'], 'spoof-device-id')
                self.assertEqual(kwargs['params']['X-Emby-Client'], 'Emby for Android')
                self.assertEqual(kwargs['params']['X-Emby-Client-Version'], '3.4.16')
                self.assertEqual(kwargs['headers']['User-Agent'], 'Mozilla/5.0 TestAndroid')
                self.assertIn('DeviceId="spoof-device-id"', kwargs['headers']['X-Emby-Authorization'])
        finally:
            configs.raw = original_config
            net_tools.requests_urllib = original_request

    def test_thin_and_full_emby_api_use_identity_when_enabled(self):
        original_config = configs.raw
        try:
            configs.raw = self.config()
            thin = EmbyApiThin(host='https://emby.example', api_key='secret', user_id='u')
            self.assertEqual(thin.headers['User-Agent'], 'Mozilla/5.0 TestAndroid')
            self.assertEqual(thin.headers['X-Emby-Device-Id'], 'spoof-device-id')
            full = EmbyApi(host='https://emby.example', api_key='secret', user_id='u')
            self.assertEqual(full.req.headers['User-Agent'], 'Mozilla/5.0 TestAndroid')
            self.assertEqual(full.req.headers['X-Emby-Client'], 'Emby for Android')
        finally:
            configs.raw = original_config


if __name__ == '__main__':
    unittest.main()
