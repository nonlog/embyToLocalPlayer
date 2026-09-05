"""Lightweight, standalone configuration UI for embyToLocalPlayer."""

import argparse
import configparser
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from utils.config_editor import update_ini_preserving_comments


BOOL_FIELDS = {
    ('emby', 'update_progress'), ('emby', 'fullscreen'),
    ('potplayer', 'controlled_instance'), ('floppy', 'enable'),
    ('floppy', 'verify_ssl'), ('dev', 'use_system_proxy'),
    ('dev', 'skip_certificate_verify'), ('dev', 'pretty_title'),
    ('dev', 'one_instance_mode'),
}

TABS = {
    'Playback': [
        ('Player', 'emby', 'player'), ('Update server progress', 'emby', 'update_progress'),
        ('Fullscreen', 'emby', 'fullscreen'), ('PotPlayer path', 'exe', 'pot'),
        ('mpv path', 'exe', 'mpv'), ('VLC path', 'exe', 'vlc'),
        ('MPC-HC path', 'exe', 'hc'), ('MPC-BE path', 'exe', 'be'),
        ('Pot extra args (JSON)', 'player_args', 'pot'),
        ('mpv extra args (JSON)', 'player_args', 'mpv'),
        ('VLC extra args (JSON)', 'player_args', 'vlc'),
        ('MPC-HC extra args (JSON)', 'player_args', 'hc'),
    ],
    'Request overrides': [
        ('Media path', 'request_override', 'media_path'),
        ('Media title', 'request_override', 'media_title'),
        ('Subtitle path / URL', 'request_override', 'sub_file'),
        ('Start seconds', 'request_override', 'start_sec'),
        ('Total seconds', 'request_override', 'total_sec'),
        ('Disk mode (yes/no; blank = unchanged)', 'request_override', 'mount_disk_mode'),
    ],
    'PotPlayer': [
        ('Direct executable', 'potplayer', 'direct_exe'),
        ('Controlled /new + /current', 'potplayer', 'controlled_instance'),
        ('Pause detect seconds', 'potplayer', 'pause_detect_seconds'),
        ('Pot profile', 'dev', 'pot_conf'),
        ('Title character mapping', 'dev', 'media_title_translate'),
    ],
    'Network & behavior': [
        ('Use system proxy', 'dev', 'use_system_proxy'),
        ('Script proxy', 'dev', 'script_proxy'), ('Player proxy', 'dev', 'player_proxy'),
        ('Redirect-check hosts', 'dev', 'redirect_check_host'),
        ('Direct .strm hosts', 'dev', 'strm_direct_host'),
        ('Force disk-mode paths', 'dev', 'force_disk_mode_path'),
        ('Skip TLS verification', 'dev', 'skip_certificate_verify'),
        ('Pretty title', 'dev', 'pretty_title'),
        ('Single ETLP player instance', 'dev', 'one_instance_mode'),
        ('Playlist hosts', 'playlist', 'enable_host'),
        ('Playlist item limit', 'playlist', 'item_limit'),
    ],
    'Floppy': [
        ('Enable', 'floppy', 'enable'), ('Base URL', 'floppy', 'base_url'),
        ('API / integration token', 'floppy', 'token'),
        ('Media-server hosts', 'floppy', 'enable_host'),
        ('Progress interval (s)', 'floppy', 'progress_interval'),
        ('Completed percent', 'floppy', 'completed_percent'),
        ('Request timeout (s)', 'floppy', 'timeout'),
        ('Verify TLS certificate', 'floppy', 'verify_ssl'),
    ],
}


def locate_config():
    root = Path(__file__).resolve().parent
    platform_name = 'Windows' if os.name == 'nt' else ('Darwin' if sys.platform == 'darwin' else 'Linux')
    for name in (f'embyToLocalPlayer-{platform_name}.ini', 'embyToLocalPlayer.ini',
                 'embyToLocalPlayer_config.ini'):
        candidate = root / name
        if candidate.exists():
            return candidate
    return root / 'embyToLocalPlayer_config.ini'


class ConfigApp:
    def __init__(self, root, path):
        self.root = root
        self.path = Path(path)
        self.vars = {}
        self.config = configparser.ConfigParser()
        self.root.title('embyToLocalPlayer Configuration')
        self.root.minsize(760, 580)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        for tab_name, fields in TABS.items():
            self._build_fields_tab(tab_name, fields)
        self._build_request_tab()
        self._build_advanced_tab()
        bar = ttk.Frame(root)
        bar.pack(fill='x', padx=10, pady=(0, 10))
        ttk.Button(bar, text='Reload', command=self.load).pack(side='left')
        ttk.Button(bar, text='Save', command=self.save).pack(side='right')
        ttk.Label(bar, text=str(self.path)).pack(side='left', padx=12)
        self.load()

    def _build_fields_tab(self, name, fields):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text=name)
        frame.columnconfigure(1, weight=1)
        for row, (label, section, option) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 10), pady=5)
            key = (section, option)
            if key in BOOL_FIELDS:
                var = tk.BooleanVar()
                ttk.Checkbutton(frame, variable=var).grid(row=row, column=1, sticky='w', pady=5)
            else:
                var = tk.StringVar()
                show = '*' if key == ('floppy', 'token') else ''
                entry = ttk.Entry(frame, textvariable=var, show=show)
                entry.grid(row=row, column=1, sticky='ew', pady=5)
                if option in ('pot', 'mpv', 'vlc', 'hc', 'be', 'direct_exe'):
                    ttk.Button(frame, text='Browse', command=lambda v=var: self._browse(v)).grid(
                        row=row, column=2, padx=(8, 0), pady=5)
            self.vars[key] = var
        if name == 'Floppy':
            ttk.Button(frame, text='Test Floppy connection', command=self.test_floppy).grid(
                row=len(fields), column=1, sticky='w', pady=(14, 0))

    def _build_request_tab(self):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text='Last request')
        ttk.Label(frame, text='Sanitized parameters most recently received from Emby/Jellyfin/Plex.').pack(anchor='w')
        self.request_text = tk.Text(frame, wrap='none', height=24)
        self.request_text.pack(fill='both', expand=True, pady=8)
        ttk.Button(frame, text='Refresh', command=self.load_request).pack(anchor='w')

    def _build_advanced_tab(self):
        frame = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(frame, text='Advanced INI')
        ttk.Label(frame, text='Full INI editor for path maps and options not exposed above.').pack(anchor='w')
        self.raw_text = tk.Text(frame, wrap='none', undo=True)
        self.raw_text.pack(fill='both', expand=True, pady=8)
        ttk.Button(frame, text='Apply raw INI', command=self.save_raw).pack(anchor='e')

    @staticmethod
    def _browse(var):
        value = filedialog.askopenfilename(title='Choose player executable')
        if value:
            var.set(value)

    def load(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.path, encoding='utf-8-sig')
        for (section, option), var in self.vars.items():
            if isinstance(var, tk.BooleanVar):
                var.set(self.config.getboolean(section, option, fallback=False))
            else:
                var.set(self.config.get(section, option, fallback=''))
        self.raw_text.delete('1.0', 'end')
        self.raw_text.insert('1.0', self.path.read_text(encoding='utf-8-sig'))
        self.load_request()

    def load_request(self):
        path = self.path.parent / '.tmp' / 'last_request.json'
        text = 'No request snapshot yet.'
        if path.exists():
            try:
                text = json.dumps(json.loads(path.read_text(encoding='utf-8')), ensure_ascii=False, indent=2)
            except (OSError, json.JSONDecodeError) as exc:
                text = f'Unable to read snapshot: {exc}'
        self.request_text.configure(state='normal')
        self.request_text.delete('1.0', 'end')
        self.request_text.insert('1.0', text)
        self.request_text.configure(state='disabled')

    def save(self):
        changes = {}
        for key, var in self.vars.items():
            value = 'yes' if isinstance(var, tk.BooleanVar) and var.get() else (
                'no' if isinstance(var, tk.BooleanVar) else var.get())
            if key[0] == 'player_args' and value.strip():
                try:
                    parsed = json.loads(value)
                    if not isinstance(parsed, list) or not all(isinstance(v, str) for v in parsed):
                        raise ValueError
                except (json.JSONDecodeError, ValueError):
                    messagebox.showerror('Invalid player args', f'{key[1]} must be a JSON array of strings.')
                    return
            changes[key] = value
        update_ini_preserving_comments(self.path, changes)
        self.load()
        messagebox.showinfo('Saved', 'Configuration saved. Restart the background service for startup-only settings.')

    def save_raw(self):
        raw = self.raw_text.get('1.0', 'end-1c')
        check = configparser.ConfigParser()
        try:
            check.read_string(raw)
        except configparser.Error as exc:
            messagebox.showerror('Invalid INI', str(exc))
            return
        self.path.write_text(raw, encoding='utf-8-sig')
        self.load()
        messagebox.showinfo('Saved', 'Raw INI saved.')

    def test_floppy(self):
        base = self.vars[('floppy', 'base_url')].get().strip().rstrip('/')
        token = self.vars[('floppy', 'token')].get().strip()
        if not base or not token:
            messagebox.showwarning('Floppy', 'Base URL and token are required.')
            return
        req = urllib.request.Request(f'{base}/api/v1/user/preferences/',
                                     headers={'X-API-Key': token, 'Accept': 'application/json'})
        verify = self.vars[('floppy', 'verify_ssl')].get()
        context = None if verify else ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                response.read(64)
            messagebox.showinfo('Floppy', 'Connection and authentication succeeded.')
        except Exception as exc:
            messagebox.showerror('Floppy', f'Connection failed: {type(exc).__name__}: {str(exc)[:160]}')


def main():
    parser = argparse.ArgumentParser(description='embyToLocalPlayer configuration GUI')
    parser.add_argument('--config', default=str(locate_config()), help='INI file to edit')
    args = parser.parse_args()
    root = tk.Tk()
    ConfigApp(root, args.config)
    root.mainloop()


if __name__ == '__main__':
    main()
