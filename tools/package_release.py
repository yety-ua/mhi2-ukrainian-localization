#!/usr/bin/env python3
"""Validate the reviewed SD overlay and create a fresh release ZIP.

Usage: python3 tools/package_release.py
Output: dist/mhi2-ukrainian-localization-k3346-v1.0.0-preview.8.zip
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / 'sd-card'
PACKAGE = CARD / 'uk-localization'


def validated_sources():
    metadata = json.loads((PACKAGE / 'package.json').read_text())
    result = {}
    lines = (PACKAGE / 'SHA1SUMS').read_text().splitlines()
    if len(lines) != 14:
        raise ValueError('Incomplete manifest')
    seen = set()
    for line in lines:
        expected, name = line.split()
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or name in seen:
            raise ValueError('Unsafe or duplicate manifest path')
        seen.add(name)
        data = (PACKAGE / path).read_bytes()
        if hashlib.sha1(data).hexdigest() != expected or hashlib.sha256(data).hexdigest() != metadata['sha256'][name]:
            raise ValueError('Unreviewed package change: ' + name)
        if name.endswith(('.zip', '.jar')):
            with zipfile.ZipFile(PACKAGE / path) as archive:
                if archive.testzip() or len(set(archive.namelist())) != len(archive.namelist()):
                    raise ValueError('Invalid archive: ' + name)
        if name.endswith(('.sh', '.awk')) and (b'\r' in data or data.startswith(b'\xef\xbb\xbf')):
            raise ValueError('LF/no BOM required: ' + name)
        result[name] = data
    if seen != set(metadata['sha256']):
        raise ValueError('Manifest and SHA-256 metadata disagree')
    if (PACKAGE / 'ACTION.txt').read_bytes() != b'CHECK\n':
        raise ValueError('Release action must be CHECK')
    for name in ('mod/custom.sh', 'mod/command.sh'):
        wrapper = (CARD / name).read_bytes()
        if b'\r' in wrapper or wrapper.startswith(b'\xef\xbb\xbf'):
            raise ValueError('Wrapper requires LF/no BOM: ' + name)
    return result


def build(output):
    validated_sources()
    if output.exists():
        raise ValueError('Output exists; use --output with a fresh filename')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(CARD.rglob('*')):
            if path.is_file():
                relative = path.relative_to(CARD)
                if any(part in ['logs', 'backups', '__pycache__'] for part in relative.parts):
                    continue
                archive.write(path, relative.as_posix())
        archive.write(ROOT / 'README.md', 'README.md')
        for path in sorted((ROOT / 'docs').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError('Release ZIP CRC failed')
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + '.sha256').write_text(checksum + '  ' + output.name + '\n', encoding='ascii')
    print(output)
    print('SHA-256: ' + checksum)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/mhi2-ukrainian-localization-k3346-v1.0.0-preview.8.zip')
    build(parser.parse_args().output.resolve())
