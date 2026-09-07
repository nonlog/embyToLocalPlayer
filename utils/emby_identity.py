"""Configurable Emby client identity overrides.

When disabled this module is intentionally inert so existing request behaviour is
preserved.  When enabled, non-empty fields override the identity values sent to
Emby in query parameters, request headers and MediaBrowser authorization.
"""

from utils.configs import configs


SECTION = 'emby_identity'


def _raw(config=None):
    return config or configs.raw


def _text(raw, option, fallback=''):
    value = raw.get(SECTION, option, fallback=fallback)
    return str(value).strip() if value is not None else ''


def enabled_for(netloc='', config=None):
    raw = _raw(config)
    if not raw.getboolean(SECTION, 'enable', fallback=False):
        return False
    hosts = _text(raw, 'enable_host', '.') or '.'
    if not netloc:
        return True
    values = [item.strip() for item in hosts.replace('，', ',').split(',') if item.strip()]
    return not values or '.' in values or any(value in netloc for value in values)


def resolve_emby_identity(*, netloc='', device_id='', device_name='', client='', version='',
                          user_agent='', config=None):
    raw = _raw(config)
    identity = {
        'enabled': enabled_for(netloc=netloc, config=raw),
        'device_id': str(device_id or ''),
        'device_name': str(device_name or ''),
        'client': str(client or ''),
        'version': str(version or ''),
        'user_agent': str(user_agent or ''),
    }
    if not identity['enabled']:
        return identity
    for key in ('device_id', 'device_name', 'client', 'version', 'user_agent'):
        override = _text(raw, key)
        if override:
            identity[key] = override
    return identity


def _escape_auth(value):
    return str(value).replace('\\', '\\\\').replace('"', '\\"')


def build_emby_authorization(token, identity):
    fields = []
    for label, key in (
        ('Client', 'client'),
        ('Device', 'device_name'),
        ('DeviceId', 'device_id'),
        ('Version', 'version'),
    ):
        value = identity.get(key)
        if value:
            fields.append(f'{label}="{_escape_auth(value)}"')
    if token:
        fields.append(f'Token="{_escape_auth(token)}"')
    return 'MediaBrowser ' + ', '.join(fields)


def identity_params(identity, *, token=''):
    """Return X-Emby identity query parameters for an enabled identity."""
    if not identity.get('enabled'):
        return {}
    params = {}
    mapping = (
        ('client', 'X-Emby-Client'),
        ('device_name', 'X-Emby-Device-Name'),
        ('device_id', 'X-Emby-Device-Id'),
        ('version', 'X-Emby-Client-Version'),
    )
    for key, header in mapping:
        value = identity.get(key)
        if value:
            params[header] = value
    if token:
        params['X-Emby-Token'] = token
    return params


def identity_headers(identity, *, token='', base=None, authorization=True):
    """Merge configured Emby identity into HTTP headers."""
    headers = dict(base or {})
    if not identity.get('enabled'):
        return headers
    params = identity_params(identity)
    headers.update(params)
    if identity.get('user_agent'):
        headers['User-Agent'] = identity['user_agent']
    if authorization:
        auth = build_emby_authorization(token, identity)
        headers['X-Emby-Authorization'] = auth
        headers['Authorization'] = auth
    return headers
