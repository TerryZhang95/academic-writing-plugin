#!/usr/bin/env python3
"""Check local figure files and digest-bound review records. Runs no drawing code."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

MAX_BYTES = 16_000_000


def resolve(root, name):
    path = Path(name)
    if not path.is_absolute():
        path = root / path
    if '..' in path.parts or path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Use ordinary files within the authorized project')
    path = path.resolve()
    if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('File is missing, outside the project, or too large')
    return path


def inspect(root, name):
    path = resolve(root, name)
    raw = path.read_bytes()
    result = {'path': path.relative_to(root).as_posix(),
              'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if path.suffix.lower() == '.png':
        if len(raw) < 33 or raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[12:16] != b'IHDR':
            raise ValueError('Invalid PNG header')
        w, h = struct.unpack('>II', raw[16:24])
        if not w or not h or b'IEND' not in raw[-16:]:
            raise ValueError('Incomplete PNG')
        result.update(format='png', dimensions=[w, h])
    elif path.suffix.lower() == '.pdf':
        if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-1024:]:
            raise ValueError('Invalid PDF envelope')
        result.update(format='pdf', dimensions=None)
    elif path.suffix.lower() == '.svg':
        passive = re.sub(br'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\s+"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">', b'', raw)
        if re.search(br'<!DOCTYPE|<!ENTITY', passive, re.I):
            raise ValueError('SVG entity declarations are not supported')
        svg = ET.fromstring(passive)
        if svg.tag.split('}')[-1] != 'svg':
            raise ValueError('Expected an SVG root')
        if any(e.tag.split('}')[-1] in ('script', 'foreignObject') or
               any(k.lower().startswith('on') or (k.split('}')[-1] == 'href' and not v.startswith(('#', 'data:image/png;base64,')))
                   for k, v in e.attrib.items()) for e in svg.iter()):
            raise ValueError('Active or externally linked SVG is not supported')
        result.update(embedded_raster=any(e.tag.split('}')[-1] == 'image' for e in svg.iter()), format='svg', dimensions=svg.attrib.get('viewBox') or
                      [svg.attrib.get('width'), svg.attrib.get('height')])
    else:
        raise ValueError('Only PNG, PDF and SVG figure records are supported')
    return result


def check(config):
    root = Path(config['project_root']).absolute()
    if root.is_symlink() or any(p.is_symlink() for p in root.parents) or not root.is_dir():
        raise ValueError('Use an authorized ordinary project directory')
    root = root.resolve()
    outputs = config.get('outputs', [])
    inputs = config.get('inputs', [])
    if not 1 <= len(outputs) <= 24 or not 1 <= len(inputs) <= 24:
        raise ValueError('Provide 1-24 explicit inputs and outputs')
    issues, sources, artifacts, seen = [], [], [], set()
    for item in inputs + ([config['script']] if config.get('script') else []):
        path = resolve(root, item['path'])
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        sources.append({'path': path.relative_to(root).as_posix(), 'sha256': actual})
        if actual != item.get('sha256'):
            issues.append({'path': sources[-1]['path'], 'reason': 'input_or_script_digest_mismatch'})
    for item in outputs:
        artifact = inspect(root, item['path'])
        path = artifact['path']
        if path in seen:
            raise ValueError('Duplicate figure output')
        seen.add(path)
        artifacts.append(artifact)
        if artifact['sha256'] != item.get('sha256'):
            issues.append({'path': path, 'reason': 'output_digest_mismatch'})
        for kind in ('data', 'visual', 'export'):
            record = item.get('checks', {}).get(kind, {})
            if (record.get('status') != 'pass' or not isinstance(record.get('evidence'), str)
                    or not record['evidence'].strip() or record.get('reviewed_sha256') != artifact['sha256']):
                issues.append({'path': path, 'reason': kind + '_review_missing_or_stale'})
    if not isinstance(config.get('rules_versions'), list) or not config['rules_versions']:
        issues.append({'reason': 'rules_versions_missing'})
    if config.get('unresolved') != []:
        issues.append({'reason': 'unresolved_findings_or_missing_record'})
    return {'contract': 'academic-figure-evidence-v1',
            'status': 'pending' if issues else 'evidence_consistent',
            'inputs': sources, 'outputs': artifacts, 'issues': issues,
            'scope': 'File headers and review-record correspondence only; no image decoding, visual judgment or scientific verification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Local UTF-8 JSON review record')
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 256000:
            raise ValueError('Review record exceeds limit')
        result = check(json.loads(args.input.read_text(encoding='utf-8')))
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['status'] == 'evidence_consistent' else 1
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
        print(json.dumps({'status': 'pending', 'reason': 'Invalid record or unavailable figure file'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
