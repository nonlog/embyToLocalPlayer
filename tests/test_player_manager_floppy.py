import configparser
import unittest

from utils.configs import configs
from utils import player_manager as pm


class FakeFloppy:
    def __init__(self):
        self.events = []

    def set_playlist_data(self, data):
        self.events.append(('playlist', data))

    def start(self, position=None):
        self.events.append(('start', position))


class PlayerManagerFloppyTests(unittest.TestCase):
    def test_playlist_scrobble_starts_only_after_playlist_setup(self):
        original_config = configs.raw
        original_start = pm.start_player_func_dict['vlc']
        original_playlist = pm.playlist_func_dict['vlc']
        try:
            cfg = configparser.ConfigParser()
            cfg.read_dict({'playlist': {'item_limit': '-1'}})
            configs.raw = cfg
            manager = object.__new__(pm.BaseManager)
            manager.data = {'start_sec': 12, 'mount_disk_mode': False, 'gui_cmd': False}
            manager.player_name = 'vlc'
            manager.player_path = 'vlc.exe'
            manager.player_kwargs = {}
            manager.floppy = FakeFloppy()
            manager.make_start_sec_correct = lambda: 12

            pm.start_player_func_dict['vlc'] = lambda **kwargs: {'pid': 1}
            pm.playlist_func_dict['vlc'] = lambda **kwargs: {'video.mkv': {'item_id': '1'}}

            manager.start_player(cmd=['vlc.exe', 'video.mkv'], start_sec=12, sub_file=None,
                                 media_title='Video', mount_disk_mode=False)
            self.assertEqual(manager.floppy.events, [])

            manager.playlist_add(eps_data=[])
            self.assertEqual(manager.floppy.events[0][0], 'playlist')
            self.assertEqual(manager.floppy.events[1], ('start', 12))
        finally:
            configs.raw = original_config
            pm.start_player_func_dict['vlc'] = original_start
            pm.playlist_func_dict['vlc'] = original_playlist


if __name__ == '__main__':
    unittest.main()
