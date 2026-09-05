import os
import re
import tempfile

SECTION_RE = re.compile(r'^\s*\[([^]]+)\]\s*$')
OPTION_RE = re.compile(r'^(\s*)([^#;][^=]*?)(\s*=\s*)(.*?)(\r?\n)?$')


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
    fd, tmp = tempfile.mkstemp(prefix='.etlp-config-', suffix='.ini', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='') as fh:
            fh.writelines(output)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
