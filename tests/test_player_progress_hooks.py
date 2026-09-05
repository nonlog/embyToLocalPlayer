import unittest
from unittest import mock

from utils import players


class FakeVLC:
    def __init__(self):
        self._items = [
            {
                'time': 10,
                'length': 100,
                'state': 'playing',
                'information': {'category': {'meta': {'filename': 'stream.mkv'}}},
            },
            {
                'time': 20,
                'length': 100,
                'state': 'paused',
                'information': {'category': {'meta': {'filename': 'stream.mkv'}}},
            },
        ]

    def get(self, *_args, **_kwargs):
        if not self._items:
            raise RuntimeError('player closed')
        return self._items.pop(0)


class FakeMPC:
    def __init__(self):
        self._items = [
            ['2', 10000, '/media/stream.mkv', 100000],
            ['1', 20000, '/media/stream.mkv', 100000],
            ['2', 30000, '/media/stream.mkv', 100000],
        ]

    def get(self, *_args, **_kwargs):
        if not self._items:
            raise RuntimeError('player closed')
        return self._items.pop(0)


class PlayerProgressHookTests(unittest.TestCase):
    @mock.patch('utils.players.time.sleep', return_value=None)
    def test_vlc_progress_callback_preserves_playlist_return_contract(self, _sleep):
        events = []
        result = players.stop_sec_vlc(
            FakeVLC(),
            stop_sec_only=False,
            progress_callback=lambda **event: events.append(event),
        )

        stop_map, total_map = result
        self.assertEqual(stop_map, {'stream.mkv': 20})
        self.assertEqual(total_map, {'stream.mkv': 100})
        self.assertEqual([event['position'] for event in events], [10, 20])
        self.assertFalse(events[0]['paused'])
        self.assertTrue(events[1]['paused'])

    @mock.patch('utils.players.time.sleep', return_value=None)
    def test_mpc_progress_callback_preserves_playlist_return_contract(self, _sleep):
        events = []
        result = players.stop_sec_mpc(
            FakeMPC(),
            stop_sec_only=False,
            progress_callback=lambda **event: events.append(event),
        )

        stop_map, total_map = result
        self.assertEqual(stop_map, {'stream.mkv': 10})
        self.assertEqual(total_map, {'stream.mkv': 100})
        self.assertEqual([event['position'] for event in events], [10, 20, 30])
        self.assertFalse(events[0]['paused'])
        self.assertTrue(events[1]['paused'])
        self.assertFalse(events[2]['paused'])


if __name__ == '__main__':
    unittest.main()
