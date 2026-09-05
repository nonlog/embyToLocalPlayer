import configparser
import unittest

from utils.configs import configs
from utils.floppy_sync import FloppyClient, FloppyPlaybackBridge


class FakeClient:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read_dict({'floppy': {'enable': 'yes', 'base_url': 'https://floppy.test',
                                          'token': 'secret', 'progress_interval': '5',
                                          'completed_percent': '90'}})
        self.events = []

    def enabled_for(self, data):
        return True

    def scrobble(self, payload, event_id=None):
        self.events.append(('scrobble', payload))

    def progress(self, payload, event_id=None):
        self.events.append(('progress', payload))


class FloppyPlaybackBridgeTests(unittest.TestCase):
    def movie(self):
        return {'item_id': '1', 'Type': 'Movie', 'ProviderIds': {'Tmdb': '603'},
                'Name': 'The Matrix', 'start_sec': 10, 'total_sec': 100,
                'netloc': 'emby.test'}

    def test_start_pause_resume_progress_and_completed_stop(self):
        client = FakeClient()
        now = [10.0]
        bridge = FloppyPlaybackBridge(self.movie(), client=client, dispatch=lambda fn: fn(),
                                      clock=lambda: now[0])
        bridge.start(10)
        bridge.observe(key='movie.mkv', position=20, duration=100, paused=True)
        now[0] = 16.0
        bridge.observe(key='movie.mkv', position=30, duration=100, paused=False)
        bridge.stop(position=95, duration=100)
        actions = [event[1].get('action') for event in client.events if event[0] == 'scrobble']
        self.assertEqual(actions, ['start', 'pause', 'start', 'stop'])
        self.assertTrue(client.events[-1][1]['completed'])
        self.assertTrue(any(event[0] == 'progress' for event in client.events))

    def test_episode_uses_series_identity_not_episode_tmdb(self):
        client = FakeClient()
        episode = {'item_id': 'e1', 'Type': 'Episode',
                   'ProviderIds': {'Tmdb': '999999', 'Tvdb': '303821'},
                   'SeriesId': 's1', 'SeriesName': 'Friends', 'Name': 'Pilot',
                   'ParentIndexNumber': 1, 'IndexNumber': 1,
                   'start_sec': 0, 'total_sec': 1200, 'netloc': 'emby.test'}
        bridge = FloppyPlaybackBridge(
            episode, client=client, dispatch=lambda fn: fn(),
            series_fetcher=lambda item: {'Name': 'Friends', 'ProviderIds': {'Tmdb': '1668'}})
        bridge.start(0)
        payload = client.events[0][1]
        self.assertEqual(payload['media_type'], 'episode')
        self.assertEqual(payload['ids'], {'tmdb': '1668'})
        self.assertEqual(payload['season_number'], 1)
        self.assertEqual(payload['episode_number'], 1)

    def test_floppy_failure_never_raises_into_playback(self):
        client = FakeClient()
        client.scrobble = lambda *args, **kwargs: (_ for _ in ()).throw(OSError('offline'))
        bridge = FloppyPlaybackBridge(self.movie(), client=client, dispatch=lambda fn: fn())
        bridge.start(0)

    def test_disabled_floppy_does_not_create_client_and_blank_numbers_use_defaults(self):
        original = configs.raw
        try:
            cfg = configparser.ConfigParser()
            cfg.read_dict({'floppy': {'enable': 'no', 'timeout': '', 'verify_ssl': '',
                                      'progress_interval': '', 'completed_percent': ''}})
            configs.raw = cfg
            bridge = FloppyPlaybackBridge(self.movie(), dispatch=lambda fn: fn())
            self.assertFalse(bridge.enabled)
            self.assertIsNone(bridge.client)
            self.assertEqual(bridge.progress_interval, 30.0)
            self.assertEqual(bridge.completed_threshold, 0.9)
        finally:
            configs.raw = original

    def test_blank_floppy_client_values_use_runtime_defaults(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({'floppy': {'enable': 'yes', 'base_url': 'https://floppy.test',
                                  'token': 'secret', 'timeout': '', 'verify_ssl': ''}})
        client = FloppyClient(config=cfg)
        self.assertEqual(client.timeout, 5.0)
        self.assertTrue(client.verify_ssl)

    def test_floppy_client_sends_runtime_user_agent(self):
        captured = {}

        class Response:
            def read(self):
                return b'{}'

        def opener(req, **kwargs):
            captured['user_agent'] = req.get_header('User-agent')
            captured['api_key'] = req.get_header('X-api-key')
            return Response()

        client = FloppyClient(base_url='https://floppy.test', token='secret', opener=opener)
        self.assertEqual(client.test_connection(), {})
        self.assertEqual(captured['user_agent'], 'embyToLocalPlayer/floppy')
        self.assertEqual(captured['api_key'], 'secret')


if __name__ == '__main__':
    unittest.main()
