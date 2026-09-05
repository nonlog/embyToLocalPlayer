import os
import re
import tempfile

SECTION_RE = re.compile(r'^\s*\[([^]]+)\]\s*$')
OPTION_RE = re.compile(r'^(\s*)([^#;][^=]*?)(\s*=\s*)(.*?)(\r?\n)?$')

GUI_BOOL_DEFAULTS = {
    ('emby', 'update_progress'): True,
    ('emby', 'fullscreen'): True,
    ('potplayer', 'controlled_instance'): True,
    ('floppy', 'enable'): False,
    ('floppy', 'verify_ssl'): True,
    ('dev', 'use_system_proxy'): True,
    ('dev', 'skip_certificate_verify'): False,
    ('dev', 'pretty_title'): True,
    ('dev', 'one_instance_mode'): True,
}

GUI_TEXT_DEFAULTS = {
    ('potplayer', 'pause_detect_seconds'): '3',
    ('floppy', 'progress_interval'): '30',
    ('floppy', 'completed_percent'): '90',
    ('floppy', 'timeout'): '5',
}


def get_boolean_with_runtime_default(config, section, option):
    default = GUI_BOOL_DEFAULTS.get((section, option), False)
    return config.getboolean(section, option, fallback=default)


def get_text_with_runtime_default(config, section, option):
    value = config.get(section, option, fallback=None)
    default = GUI_TEXT_DEFAULTS.get((section, option), '')
    if value is None or (not str(value).strip() and (section, option) in GUI_TEXT_DEFAULTS):
        return default
    return str(value)


def update_ini_preserving_comments(path, changes):
    with open(path, 'r', encoding='utf-8-sig', newline='') as fh:
        lines = fh.readlines()
    pending = {(str(s).lower(), str(o).lower()): str(v) for (s, o), v in changes.items()}
    section = None
    output = []

    def append_missing(current):
        for (sec, option), value in list(pending.items()):
            if sec == current:
                output.append(f'{option} = {value}\n')
                pending.pop((sec, option), None)

    for line in lines:
        section_match = SECTION_RE.match(line.strip('\r\n'))
        if section_match:
            if section is not None:
                append_missing(section)
            section = section_match.group(1).lower()
            output.append(line)
            continue
        option_match = OPTION_RE.match(line)
        if section and option_match:
            key = (section, option_match.group(2).strip().lower())
            if key in pending:
                newline = option_match.group(5) or '\n'
                output.append(f'{option_match.group(1)}{option_match.group(2).strip()}'
                              f'{option_match.group(3)}{pending.pop(key)}{newline}')
                continue
        output.append(line)
    if section is not None:
        append_missing(section)

    by_section = {}
    for (sec, option), value in pending.items():
        by_section.setdefault(sec, []).append((option, value))
    for sec, options in by_section.items():
        if output and output[-1].strip():
            output.append('\n')
        output.append(f'[{sec}]\n')
        output.extend(f'{option} = {value}\n' for option, value in options)

    directory = os.path.dirname(os.path.abspath(path))
    preserve_link = os.path.islink(path)
    try:
        preserve_link = preserve_link or os.stat(path).st_nlink > 1
    except OSError:
        pass
    if preserve_link:
        # Scoop persists files using filesystem links. Replacing the path would
        # silently break that link and split the runtime config from persist.
        with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
            fh.writelines(output)
            fh.flush()
            os.fsync(fh.fileno())
        return

    fd, tmp = tempfile.mkstemp(prefix='.etlp-config-', suffix='.ini', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='') as fh:
            fh.writelines(output)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
