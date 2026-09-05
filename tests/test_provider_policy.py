import unittest

from utils.provider_policy import STARTUP_PROBE_PROVIDERS
from utils.tools import show_version_info


class ProviderPolicyTests(unittest.TestCase):
    def test_trakt_is_not_probed_at_startup(self):
        self.assertNotIn('trakt', STARTUP_PROBE_PROVIDERS)
        self.assertIn('bangumi', STARTUP_PROBE_PROVIDERS)
        self.assertIn('simkl', STARTUP_PROBE_PROVIDERS)

    def test_fork_version_matches_patch_release(self):
        self.assertEqual(show_version_info(), '2026.09.05.6')


if __name__ == '__main__':
    unittest.main()
