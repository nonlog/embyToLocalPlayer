"""Startup policy for optional third-party sync providers."""

# Trakt is intentionally lazy: authentication/API access only happens when a
# completed playback item matches [trakt] enable_host. Probing Trakt at process
# startup causes unnecessary external requests and can fail independently of
# local playback (for example, HTTP 403 from api.trakt.tv).
STARTUP_PROBE_PROVIDERS = ('bangumi', 'simkl')
