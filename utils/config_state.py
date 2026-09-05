import json
import os
import tempfile
import urllib.parse

from utils.configs import configs

SENSITIVE_QUERY_KEYS = {'api_key', 'token', 'x-emby-token', 'x-plex-token', 'authorization'}


def sanitize_url(value):
    if not isinstance(value, str) or not value.lower().startswith(('http://', 'https://')):
        return value
    parsed = urllib.parse.urlsplit(value)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    safe = [(key, '[REDACTED]' if key.lower() in SENSITIVE_QUERY_KEYS else val)
            for key, val in query]
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                                    urllib.parse.urlencode(safe), parsed.fragment))


def request_snapshot(data):
    keys = ('server', 'server_version', 'netloc', 'file_path', 'media_path', 'stream_url',
            'start_sec', 'total_sec', 'media_title', 'sub_file', 'mount_disk_mode', 'item_id',
            'media_source_id', 'play_session_id', 'Type', 'SeriesName', 'ParentIndexNumber',
            'IndexNumber', 'ProviderIds')
    source = dict(data.get('main_ep_info') or {})
    source.update(data)
    result = {}
    for key in keys:
        if key not in source:
            continue
        value = source[key]
        if key == 'play_session_id':
            value = '[REDACTED]'
        elif isinstance(value, str):
            value = sanitize_url(value)
        result[key] = value
    return result


def save_request_snapshot(data, path=None):
    path = path or os.path.join(configs.cwd, '.tmp', 'last_request.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.last-request-', suffix='.json', dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            json.dump(request_snapshot(data), fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path
