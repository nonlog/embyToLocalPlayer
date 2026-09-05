import json
import queue
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from utils.configs import MyLogger, configs

logger = MyLogger()
SUPPORTED_IDS = ('tmdb', 'imdb', 'tvdb')


def _provider_ids(data):
    raw = data.get('ProviderIds') or {}
    return {str(k).lower(): str(v) for k, v in raw.items()
            if str(k).lower() in SUPPORTED_IDS and v not in (None, '')}


def _media_source(data):
    merged = dict(data.get('main_ep_info') or {})
    merged.update({k: v for k, v in data.items() if v is not None})
    return merged


def _completion(position, duration, threshold):
    if position is None or not duration or duration == 86400:
        return False
    return max(0.0, float(position)) / float(duration) >= threshold


class FloppyClient:
    def __init__(self, *, base_url=None, token=None, timeout=None, verify_ssl=None,
                 opener=None, config=None):
        raw = config or configs.raw
        self.config = raw
        self.base_url = (base_url if base_url is not None else
                         raw.get('floppy', 'base_url', fallback='')).strip().rstrip('/')
        self.token = (token if token is not None else
                      raw.get('floppy', 'token', fallback='')).strip()
        self.timeout = float(timeout if timeout is not None else
                             raw.getfloat('floppy', 'timeout', fallback=5))
        self.verify_ssl = bool(verify_ssl if verify_ssl is not None else
                               raw.getboolean('floppy', 'verify_ssl', fallback=True))
        self.opener = opener or urllib.request.urlopen

    def enabled_for(self, data):
        if not self.config.getboolean('floppy', 'enable', fallback=False):
            return False
        if not self.base_url or not self.token:
            return False
        host_rules = self.config.get('floppy', 'enable_host', fallback='.').strip()
        if not host_rules or host_rules == '.':
            return True
        netloc = str(data.get('netloc') or '')
        rules = [i.strip() for i in host_rules.replace('，', ',').split(',') if i.strip()]
        return any(rule in netloc for rule in rules)

    def _request(self, method, path, payload=None, event_id=None):
        body = json.dumps(payload).encode('utf-8') if payload is not None else None
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json',
                   'X-API-Key': self.token, 'User-Agent': 'embyToLocalPlayer/floppy'}
        if event_id:
            headers['Idempotency-Key'] = event_id
        req = urllib.request.Request(f'{self.base_url}{path}', data=body,
                                     headers=headers, method=method)
        context = None
        if req.full_url.startswith('https://') and not self.verify_ssl:
            context = ssl._create_unverified_context()
        try:
            res = self.opener(req, timeout=self.timeout, context=context)
        except TypeError:
            res = self.opener(req, timeout=self.timeout)
        raw = res.read()
        return json.loads(raw.decode('utf-8')) if raw else {}

    def scrobble(self, payload, event_id=None):
        return self._request('POST', '/api/v1/scrobble/', payload, event_id)

    def progress(self, payload, event_id=None):
        return self._request('PUT', '/api/v1/playback/progress/', payload, event_id)

    def test_connection(self):
        return self._request('GET', '/api/v1/user/preferences/')


class FloppyPlaybackBridge:
    def __init__(self, data, *, client=None, dispatch=None, clock=None, series_fetcher=None):
        self.data = data
        self.client = client or FloppyClient()
        self.enabled = self.client.enabled_for(data)
        self._queue = None
        self._queue_thread = None
        self._external_dispatch = dispatch
        self.dispatch = dispatch or self._queue_dispatch
        self.clock = clock or time.monotonic
        self.series_fetcher = series_fetcher or self._fetch_series_info
        raw = getattr(self.client, 'config', configs.raw)
        self.progress_interval = max(5.0, float(raw.getfloat('floppy', 'progress_interval', fallback=30)))
        percent = float(raw.getfloat('floppy', 'completed_percent', fallback=90))
        self.completed_threshold = min(1.0, max(0.0, percent / 100.0))
        self.playlist_data = {}
        self._active_key = None
        self._active_item = None
        self._last_position = None
        self._last_duration = None
        self._last_progress_at = 0.0
        self._paused = False
        self._series_cache = {}
        self._stopped_keys = set()

    def _queue_dispatch(self, fn):
        if self._queue is None:
            self._queue = queue.SimpleQueue()

            def worker_loop():
                while True:
                    task = self._queue.get()
                    if task is None:
                        return
                    task()

            self._queue_thread = threading.Thread(target=worker_loop, daemon=True)
            self._queue_thread.start()
        self._queue.put(fn)

    def _close_dispatch(self):
        if self._external_dispatch is None and self._queue is not None:
            self._queue.put(None)

    def set_playlist_data(self, playlist_data):
        self.playlist_data = playlist_data or {}

    def _fetch_series_info(self, item):
        series_id = item.get('SeriesId')
        if not series_id or item.get('server') == 'plex':
            return {}
        if series_id in self._series_cache:
            return self._series_cache[series_id]
        from utils.net_tools import requests_urllib
        extra = '/emby' if item.get('server') == 'emby' else ''
        params = {'X-Emby-Token': item.get('api_key', '')}
        headers = {'accept': 'application/json'}
        headers.update(item.get('headers') or {})
        url = (f"{item.get('scheme')}://{item.get('netloc')}{extra}/Users/"
               f"{item.get('user_id')}/Items/{series_id}")
        info = requests_urllib(url, params=params, headers=headers, get_json=True, timeout=5)
        self._series_cache[series_id] = info or {}
        return self._series_cache[series_id]

    def _identity(self, item):
        source = _media_source(item)
        media_type = str(source.get('Type') or '').lower()
        if media_type not in ('movie', 'episode'):
            return None
        ids = _provider_ids(source)
        series = {}
        if media_type == 'episode':
            try:
                series = self.series_fetcher(source) or {}
            except Exception:
                series = {}
            series_ids = _provider_ids(series)
            if series_ids:
                ids = series_ids
            else:
                ids = {k: v for k, v in ids.items() if k in ('imdb', 'tvdb')}
        if not ids:
            return None
        payload = {'media_type': media_type, 'ids': ids}
        if media_type == 'episode':
            season = source.get('ParentIndexNumber')
            episode = source.get('IndexNumber', source.get('index'))
            if season is None or episode is None:
                return None
            payload.update({'season_number': int(season), 'episode_number': int(episode),
                            'series_title': source.get('SeriesName') or series.get('Name'),
                            'title': source.get('Name')})
        else:
            payload['title'] = source.get('Name') or source.get('media_title')
        return {k: v for k, v in payload.items() if v not in (None, '')}

    def _item_for_key(self, key):
        if key is not None:
            item = self.playlist_data.get(key)
            if item:
                return item
            normalized = urllib.parse.unquote(str(key))
            for candidate_key, candidate in self.playlist_data.items():
                aliases = {str(candidate_key), str(candidate.get('media_title') or ''),
                           str(candidate.get('basename') or ''),
                           str(candidate.get('media_basename') or '')}
                if normalized in aliases:
                    return candidate
        return self.data

    @staticmethod
    def _item_key(item):
        return str(item.get('item_id') or item.get('Id') or
                   item.get('file_path') or item.get('media_title'))

    def _send(self, kind, item, *, action=None, position=None, duration=None, completed=None):
        if not self.enabled:
            return

        def worker():
            try:
                base = self._identity(item)
                if not base:
                    logger.info('floppy: media identity unavailable, skip event')
                    return
                event_id = f'etlp-{uuid.uuid4()}'
                if kind == 'scrobble':
                    payload = dict(base, action=action)
                    if position is not None:
                        payload['position_seconds'] = max(0, int(position))
                    if duration and duration != 86400:
                        payload['duration_seconds'] = max(0, int(duration))
                    if completed is not None:
                        payload['completed'] = bool(completed)
                    self.client.scrobble(payload, event_id=event_id)
                else:
                    if position is None:
                        return
                    payload = dict(base, position_seconds=max(0, int(position)))
                    if duration and duration != 86400:
                        payload['duration_seconds'] = max(0, int(duration))
                    payload['completed'] = bool(completed)
                    self.client.progress(payload, event_id=event_id)
            except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError) as exc:
                logger.warn(f'floppy: {kind} failed: {type(exc).__name__}: {str(exc)[:120]}')
            except Exception as exc:
                logger.warn(f'floppy: {kind} skipped after unexpected error: {type(exc).__name__}')

        self.dispatch(worker)

    def start(self, position=None):
        if not self.enabled:
            return
        item = self.data
        self._active_item = item
        self._active_key = self._item_key(item)
        self._last_position = position if position is not None else item.get('start_sec', 0)
        self._last_duration = item.get('total_sec')
        self._paused = False
        self._send('scrobble', item, action='start', position=self._last_position,
                   duration=self._last_duration)

    def observe(self, *, key=None, position=None, duration=None, paused=None):
        if not self.enabled or position is None:
            return
        item = self._item_for_key(key)
        item_key = self._item_key(item)
        if self._active_key is None:
            self._active_item, self._active_key = item, item_key
            self._send('scrobble', item, action='start', position=position, duration=duration)
        elif item_key != self._active_key:
            self._finish_active()
            self._active_item, self._active_key = item, item_key
            self._paused = False
            self._last_progress_at = 0.0
            self._send('scrobble', item, action='start', position=position, duration=duration)

        self._last_position = position
        self._last_duration = duration or item.get('total_sec')
        if paused is not None and bool(paused) != self._paused:
            self._paused = bool(paused)
            self._send('scrobble', item, action='pause' if self._paused else 'start',
                       position=position, duration=self._last_duration)

        now = self.clock()
        if now - self._last_progress_at >= self.progress_interval:
            self._last_progress_at = now
            completed = _completion(position, self._last_duration, self.completed_threshold)
            self._send('progress', item, position=position, duration=self._last_duration,
                       completed=completed)

    def _finish_active(self, *, position=None, duration=None):
        item = self._active_item
        if not self.enabled or not item:
            return
        key = self._item_key(item)
        if key in self._stopped_keys:
            return
        position = self._last_position if position is None else position
        duration = self._last_duration if duration is None else duration
        completed = _completion(position, duration, self.completed_threshold)
        self._send('scrobble', item, action='stop', position=position, duration=duration,
                   completed=completed)
        self._stopped_keys.add(key)

    def stop(self, position=None, duration=None):
        self._finish_active(position=position, duration=duration)
        self._close_dispatch()

    def finish_playlist(self, positions, durations=None):
        if not self.enabled:
            return
        durations = durations or {}
        for key, position in (positions or {}).items():
            item = self._item_for_key(key)
            item_key = self._item_key(item)
            if item_key in self._stopped_keys or position is None:
                continue
            duration = durations.get(key) or item.get('total_sec')
            completed = _completion(position, duration, self.completed_threshold)
            self._send('scrobble', item, action='stop', position=position, duration=duration,
                       completed=completed)
            self._stopped_keys.add(item_key)
        self._finish_active()
        self._close_dispatch()
