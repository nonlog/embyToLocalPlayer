import configparser
import tempfile
import unittest
from pathlib import Path

from utils.config_editor import get_boolean_with_runtime_default, update_ini_preserving_comments
from utils.config_state import request_snapshot
from utils.configs import Configs, configs
from utils.request_overrides import apply_request_overrides
from utils import players


class ConfigAndPotTests(unittest.TestCase):
    def test_gui_boolean_defaults_match_runtime_defaults(self):
        conf = configparser.ConfigParser()
        self.assertTrue(get_boolean_with_runtime_default(conf, 'emby', 'update_progress'))
        self.assertTrue(get_boolean_with_runtime_default(conf, 'emby', 'fullscreen'))
        self.assertTrue(get_boolean_with_runtime_default(conf, 'potplayer', 'controlled_instance'))
        self.assertFalse(get_boolean_with_runtime_default(conf, 'floppy', 'enable'))
        self.assertTrue(get_boolean_with_runtime_default(conf, 'floppy', 'verify_ssl'))
        self.assertTrue(get_boolean_with_runtime_default(conf, 'dev', 'use_system_proxy'))
        self.assertFalse(get_boolean_with_runtime_default(conf, 'dev', 'skip_certificate_verify'))
        self.assertTrue(get_boolean_with_runtime_default(conf, 'dev', 'pretty_title'))
        self.assertTrue(get_boolean_with_runtime_default(conf, 'dev', 'one_instance_mode'))

    def test_line_preserving_editor_keeps_comments(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'x.ini'
            path.write_text('# keep me\n[emby]\nplayer = pot\n', encoding='utf-8')
            update_ini_preserving_comments(path, {('emby', 'player'): 'mpv', ('floppy', 'enable'): 'yes'})
            text = path.read_text(encoding='utf-8-sig')
            self.assertIn('# keep me', text)
            self.assertIn('player = mpv', text)
            self.assertIn('[floppy]', text)

    def test_request_snapshot_redacts_sensitive_url_query(self):
        snap = request_snapshot({'stream_url': 'https://x/video.mkv?api_key=abc&ok=1',
                                 'play_session_id': 'private'})
        self.assertNotIn('abc', snap['stream_url'])
        self.assertEqual(snap['play_session_id'], '[REDACTED]')

    def test_localized_pot_history_detects_modern_version(self):
        with tempfile.TemporaryDirectory() as td:
            exe = Path(td) / 'PotPlayerMini64.exe'
            exe.touch()
            history = exe.parent / 'History'
            history.mkdir()
            (history / 'Chinese.txt').write_text('[260401]\nchanges\n', encoding='utf-8')
            obj = object.__new__(Configs)
            obj.raw = configparser.ConfigParser()
            obj.raw.read_dict({'emby': {'player': 'pot'}, 'exe': {'pot': str(exe)}})
            self.assertEqual(obj._pot_version_is_too_high(), '260401')

    def test_pot_title_translation_is_version_specific(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            exe = root / 'PotPlayerMini64.exe'
            exe.touch()
            history = root / 'History'
            history.mkdir()
            version_file = history / 'Chinese.txt'
            obj = object.__new__(Configs)
            obj.raw = configparser.ConfigParser()
            obj.raw.read_dict({'emby': {'player': 'pot'}, 'exe': {'pot': str(exe)}, 'dev': {}})

            version_file.write_text('[240618]\nchanges\n', encoding='utf-8')
            old_title = obj.media_title_translate('A "Quoted" Title', player_path=str(exe), log=False)
            self.assertEqual(old_title, 'A ＂Quoted＂ Title')

            version_file.write_text('[251126]\nchanges\n', encoding='utf-8')
            new_title = obj.media_title_translate("A 'Quoted' \"Title\"", player_path=str(exe), log=False)
            self.assertEqual(new_title, 'A-＇Quoted＇-＂Title＂')

    def test_pot_instance_arguments_and_stream_alias(self):
        original = configs.raw
        try:
            cfg = configparser.ConfigParser()
            cfg.read_dict({'potplayer': {'controlled_instance': 'yes'}})
            configs.raw = cfg
            start = ['PotPlayerMini64.exe', 'https://x/stream.mkv']
            players._pot_add_instance_arg(start, 'new')
            self.assertIn('/new', start)
            add = ['PotPlayerMini64.exe', 'https://x/stream.mkv']
            players._pot_add_instance_arg(add, 'current')
            self.assertIn('/current', add)
            aliases = players._pot_playlist_aliases({'media_title': 'Pretty', 'basename': 'real.mkv',
                                                      'media_basename': 'stream.mkv',
                                                      'media_path': 'https://x/stream.mkv?token=x'})
            self.assertIn('stream.mkv', aliases)
        finally:
            configs.raw = original

    def test_player_extra_args_are_json_only(self):
        obj = object.__new__(Configs)
        obj.raw = configparser.ConfigParser()
        obj.raw.read_dict({'player_args': {'pot': '["/volume=70", "/new"]'}})
        self.assertEqual(obj.player_extra_args('pot'), ['/volume=70', '/new'])

    def test_request_overrides_only_replace_explicit_values(self):
        cfg = configparser.ConfigParser()
        cfg.read_dict({'request_override': {'start_sec': '12.5', 'media_title': 'Override',
                                             'mount_disk_mode': 'yes', 'media_path': ''}})
        data = {'start_sec': 0, 'media_title': 'Original', 'mount_disk_mode': False,
                'media_path': 'https://example/video.mkv'}
        apply_request_overrides(data, cfg)
        self.assertEqual(data['start_sec'], 12.5)
        self.assertEqual(data['media_title'], 'Override')
        self.assertTrue(data['mount_disk_mode'])
        self.assertEqual(data['media_path'], 'https://example/video.mkv')


if __name__ == '__main__':
    unittest.main()
