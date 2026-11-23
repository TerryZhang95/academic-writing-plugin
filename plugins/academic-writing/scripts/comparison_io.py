"""Validate the public comparison v2 wire format. No content classification."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

CONTRACT = 'academic-comparison-v2'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def obj(value, required, optional=()):
    require(type(value) is dict and set(required) <= set(value) and not set(value) - set(required) - set(optional), 'Invalid object fields')


def text(value):
    require(type(value) is str and bool(value.strip()) and len(value) <= 4000, 'Invalid text')
    require(not re.search(r'/(?:Users|home)/|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://', value), 'Shareable data cannot contain local paths')


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value), 'Invalid ID')


def strings(value):
    require(type(value) is list and 0 < len(value) <= 100, 'Expected nonempty text list')
    for item in value: text(item)


def unique(rows):
    require(type(rows) is list and 0 < len(rows) <= 200, 'Invalid record list')
    seen = set()
    for row in rows:
        require(type(row) is dict and 'id' in row, 'Missing record ID')
        identifier(row['id'])
        require(row['id'] not in seen, 'Duplicate ID')
        seen.add(row['id'])
    return seen


def validate(data):
    obj(data, ('schema_version', 'mode', 'title', 'label', 'sources', 'columns', 'papers'), ('synthetic', 'verified_cite_keys'))
    require(type(data['schema_version']) is int and data['schema_version'] == 2, 'Requires schema_version 2; convert v1 explicitly')
    require(data['mode'] in ('coverage', 'method'), 'Invalid mode')
    for key in ('title', 'label'): text(data[key])
    require(re.fullmatch(r'[A-Za-z][A-Za-z0-9:_-]{0,95}', data['label']), 'Invalid table label')
    if 'synthetic' in data: require(type(data['synthetic']) is bool, 'Invalid synthetic flag')
    keys = data.get('verified_cite_keys', [])
    require(type(keys) is list and len(keys) == len(set(keys)), 'Invalid citation keys')
    for key in keys:
        require(type(key) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9:_-]{0,95}', key), 'Invalid citation key')
    sources = unique(data['sources']); columns = unique(data['columns']); unique(data['papers'])
    source_map = {s['id']: s for s in data['sources']}
    for s in data['sources']:
        obj(s, ('id', 'title', 'version', 'availability', 'read_scope'), ('url', 'sha256', 'page_count'))
        for k in ('title', 'version', 'read_scope'): text(s[k])
        require(s['availability'] in ('full', 'partial', 'unavailable'), 'Invalid availability')
        if 'url' in s:
            text(s['url']); u = urlsplit(s['url'])
            require(u.scheme == 'https' and u.hostname and not u.username and not u.password and not u.query and not u.fragment, 'Use public HTTPS identity URL without query or credentials')
        if 'sha256' in s: require(type(s['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', s['sha256']), 'Invalid digest')
        if 'page_count' in s: require(type(s['page_count']) is int and s['page_count'] > 0, 'Invalid page count')
    closed = set(); last = None
    for col in data['columns']:
        obj(col, ('id', 'label', 'kind', 'definition'), ('group',))
        for k in ('label', 'definition'): text(col[k])
        require(col['kind'] in (('coverage', 'text') if data['mode'] == 'coverage' else ('binary', 'value', 'text')), 'Invalid column kind')
        group = col.get('group', '')
        if group: text(group)
        if group != last:
            require(not group or group not in closed, 'Noncontiguous group')
            if last: closed.add(last)
            last = group
    counts = {}
    for row in data['papers']:
        obj(row, ('id', 'label', 'source_ids', 'cells'), ('cite_key', 'is_ours'))
        text(row['label']); strings(row['source_ids'])
        require(len(row['source_ids']) == len(set(row['source_ids'])) and set(row['source_ids']) <= sources, 'Invalid row sources')
        if 'is_ours' in row: require(type(row['is_ours']) is bool, 'Invalid author flag')
        if 'cite_key' in row: require(row['cite_key'] in keys, 'Citation key must be declared verified')
        require(type(row['cells']) is dict and set(row['cells']) == columns, 'Missing or extra cell')
        for col in data['columns']:
            cell = row['cells'][col['id']]
            obj(cell, ('status', 'reason', 'evidence'), ('basis', 'value', 'unit', 'conditions', 'notes', 'review'))
            status = cell['status']; kind = col['kind']
            allowed = {'unknown', 'nr', 'na'} | ({'full', 'partial', 'none'} if kind == 'coverage' else {'yes', 'partial', 'no'} if kind == 'binary' else {'value'})
            require(type(status) is str and status in allowed, 'Invalid status/kind combination')
            counts[status] = counts.get(status, 0) + 1
            text(cell['reason'])
            require(type(cell['evidence']) is list and len(cell['evidence']) <= 20, 'Invalid evidence list')
            if status != 'unknown':
                require(cell.get('basis') in ('explicit', 'inference') and cell['evidence'], 'Assessed cells need basis and evidence')
            elif 'basis' in cell: require(cell['basis'] in ('explicit', 'inference'), 'Invalid basis')
            if status == 'value':
                text(cell.get('value'))
                if kind == 'value':
                    text(cell.get('unit')); text(cell.get('conditions'))
            elif 'value' in cell or 'unit' in cell:
                raise ValueError('Value/unit require value status')
            for k in ('conditions',):
                if k in cell: text(cell[k])
            if 'notes' in cell: strings(cell['notes'])
            if (status in ('no', 'none', 'nr') and cell.get('basis') == 'inference') or (status == 'nr' and kind == 'value'):
                require('review' in cell, 'Negative inference requires bounded review')
            if 'review' in cell:
                obj(cell['review'], ('sections', 'terms', 'note'))
                strings(cell['review']['sections']); strings(cell['review']['terms']); text(cell['review']['note'])
            for e in cell['evidence']:
                obj(e, ('source_id', 'locator', 'quote'), ('pdf_pages',))
                require(type(e['source_id']) is str and e['source_id'] in row['source_ids'], 'Cross-row evidence reference')
                text(e['locator']); text(e['quote']); require(len(e['quote']) <= 600, 'Use short evidence excerpts')
                require(source_map[e['source_id']]['availability'] != 'unavailable', 'Unavailable source cannot supply evidence')
                if 'pdf_pages' in e:
                    pages = e['pdf_pages']; maximum = source_map[e['source_id']].get('page_count', 0)
                    require(type(pages) is list and pages and maximum and all(type(p) is int and 1 <= p <= maximum for p in pages), 'Invalid physical PDF pages')
    return {'contract': CONTRACT, 'counts': counts, 'semantic_review': 'not-performed-by-helper'}


def load(path):
    raw = Path(path).read_bytes()
    require(len(raw) <= 2_000_000, 'Comparison exceeds input size limit')
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key'); result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs)
    validate(value)
    return value
