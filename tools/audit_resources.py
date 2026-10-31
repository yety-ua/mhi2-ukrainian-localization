#!/usr/bin/env python3
"""Audit released string tables against the reviewed A4 K3346 baseline.

Usage: python3 tools/audit_resources.py --output docs/resource-audit.json
This checks structure and candidate counts, not semantic or screen completeness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'sd-card/mod/uk-localization'


def unpack(data):
    if len(data) < 8:
        raise ValueError('Truncated table')
    count = struct.unpack_from('>I', data)[0]
    if count > (len(data) - 8) // 4:
        raise ValueError('Invalid table count')
    offsets = struct.unpack_from('>' + 'I' * (count + 1), data, 4)
    start = 4 + 4 * (count + 1)
    if offsets[0] or any(a > b for a, b in zip(offsets, offsets[1:])):
        raise ValueError('Invalid table offsets')
    end = start + offsets[-1]
    if end == len(data):
        flags = None
    elif end + count == len(data):
        flags = list(data[end:])
    else:
        raise ValueError('Invalid table size')
    return [data[start + offsets[i]:start + offsets[i+1]].decode('utf-8') for i in range(count)], flags


def pack(strings, flags):
    encoded = [s.encode('utf-8') for s in strings]
    offsets = [0]
    for item in encoded:
        offsets.append(offsets[-1] + len(item))
    return (struct.pack('>I', len(strings)) + struct.pack('>' + 'I' * len(offsets), *offsets)
            + b''.join(encoded) + (bytes(flags) if flags is not None else b''))


def audit():
    path = PACKAGE / 'payload/lang_data.zip'
    with zipfile.ZipFile(path) as released, zipfile.ZipFile(PACKAGE / 'stock/lang_data.zip') as stock:
        if released.testzip() or stock.testzip():
            raise ValueError('ZIP CRC failed')
        if len(set(released.namelist())) != len(released.namelist()):
            raise ValueError('Duplicate ZIP entries')
        modules = sorted({n.split('/')[1] for n in stock.namelist() if n.startswith('resources/') and n.endswith('.data')})
        expected = set(stock.namelist()) | {'resources/' + m + '/strings_uk_UA.data' for m in modules}
        if set(released.namelist()) != expected:
            raise ValueError('Unexpected entry set')
        changed_stock = []
        for name in stock.namelist():
            if stock.read(name) == released.read(name):
                continue
            a, af = unpack(stock.read(name))
            b, bf = unpack(released.read(name))
            # Appended language-name slots: Українська (1490), then British and American English (1491, 1492).
            loc = name.rsplit('strings_', 1)[1][:-5]
            names = ('Британська англійська', 'Американська англійська') if loc == 'uk_UA' else ('English (UK)', 'English (US)')
            if (not name.startswith('resources/HMISettingsEvoHigh/strings_') or len(b) != len(a) + 3
                    or b[:-3] != a or (bf[:-3] if bf else None) != af or tuple(b[-3:]) != ('Українська',) + names):
                raise ValueError('Unexpected stock change: ' + name)
            changed_stock.append(name)
        tables = 0
        for name in released.namelist():
            if name.endswith('.data'):
                strings, flags = unpack(released.read(name))
                if pack(strings, flags) != released.read(name):
                    raise ValueError('Round-trip mismatch: ' + name)
                tables += 1
        details = []
        terminology = []
        a3_tokens = re.compile(r'\b(?:A3|AU37x|AU370|G21|Sportback|e-tron|magnetic ride)\b', re.I)
        for module in modules:
            en, flags = unpack(stock.read(f'resources/{module}/strings_en_GB.data'))
            uk, uf = unpack(released.read(f'resources/{module}/strings_uk_UA.data'))
            if module == 'HMISettingsEvoHigh':
                uk = uk[:-3]
                uf = uf[:-3] if uf else None
            if len(uk) != len(en) or uf != flags or list(map(bool, uk)) != list(map(bool, en)):
                raise ValueError('Target slot/flag/empty shape differs: ' + module)
            counts = {'module': module, 'nonempty_slots': 0, 'non_cyrillic_candidates': 0,
                      'same_as_english_candidates': 0, 'differing_candidates': 0}
            for slot, (source, target) in enumerate(zip(en, uk)):
                if not source:
                    continue
                for pattern in [r'<[^>]+>', r'%\d']:
                    if sorted(re.findall(pattern, source)) != sorted(re.findall(pattern, target)):
                        raise ValueError(f'Markup/placeholder mismatch: {module}/{slot}')
                if '|' in target and '|' not in source:
                    raise ValueError(f'Unexpected delimiter: {module}/{slot}')
                counts['nonempty_slots'] += 1
                if not re.search('[\u0400-\u04ff]', target):
                    counts['non_cyrillic_candidates'] += 1
                    counts['same_as_english_candidates' if source == target else 'differing_candidates'] += 1
                if a3_tokens.search(target):
                    tokens = [m.group().lower() for m in a3_tokens.finditer(target)]
                    terminology.append({'module': module, 'slot': slot, 'source': source, 'ukrainian': target,
                                        'tokens_already_in_target_source': all(token in source.lower() for token in tokens)})
            details.append(counts)
        return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'entries': len(released.namelist()),
                'modules': len(modules), 'tables': tables,
                'nonempty_stock_counterpart_slots': sum(d['nonempty_slots'] for d in details),
                'appended_language_name_slots': 3,
                'non_cyrillic_candidates': sum(d['non_cyrillic_candidates'] for d in details),
                'same_as_english_candidates': sum(d['same_as_english_candidates'] for d in details),
                'differing_candidates': sum(d['differing_candidates'] for d in details),
                'stock_locale_changes': 'Only appended Ukrainian, British English and American English language names in HMISettingsEvoHigh',
                'target_structure': 'All 22 Ukrainian modules preserve A4 K3346 slot, flag, empty and placeholder structure',
                'model_token_audit': terminology, 'errors': [], 'modules_detail': details,
                'note': 'Candidate counts include brands, numbers, diagnostics, proper names and intentional English speech commands. Not a translation-completeness percentage.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = audit()
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ['modules_detail', 'model_token_audit']}, indent=2))
