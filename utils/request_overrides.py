from utils.configs import configs


def _as_bool(value):
    value = value.strip().lower()
    if value in ('1', 'yes', 'true', 'on'):
        return True
    if value in ('0', 'no', 'false', 'off'):
        return False
    raise ValueError(f'invalid boolean override: {value}')


def apply_request_overrides(data, raw=None):
    """Apply explicit, persisted overrides to safe playback-request fields."""
    raw = raw or configs.raw
    if not raw.has_section('request_override'):
        return data
    converters = {
        'media_path': str,
        'media_title': str,
        'sub_file': str,
        'start_sec': float,
        'total_sec': float,
        'mount_disk_mode': _as_bool,
    }
    for key, converter in converters.items():
        value = raw.get('request_override', key, fallback='')
        if value == '':
            continue
        data[key] = converter(value)
    return data
