"""Optional PDF transcription checks; hashes and exact normalized page text only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import unicodedata
from comparison_io import load, require


def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', value).split())


def check(data, source_map):
    require(type(source_map) is dict and all(type(k) is str and type(v) is str for k,v in source_map.items()), 'Invalid private source map')
    reports = []
    sources = {s['id']:s for s in data['sources']}
    cache = {}
    for row in data['papers']:
        for col,cell in row['cells'].items():
            for index,e in enumerate(cell['evidence']):
                sid=e['source_id']; s=sources[sid]
                item={'row_id':row['id'],'column_id':col,'evidence_index':index,'source_id':sid,'status':'pending'}
                path=Path(source_map[sid]) if sid in source_map else None
                if path is None or not path.is_file():item['status']='missing-source'
                elif not s.get('sha256'):item['status']='missing-hash'
                elif hashlib.sha256(path.read_bytes()).hexdigest()!=s['sha256']:item['status']='hash-mismatch'
                elif not e.get('pdf_pages'):item['status']='missing-pages'
                else:
                    chunks=[]
                    try:
                        for page in e['pdf_pages']:
                            key=(sid,page)
                            if key not in cache:
                                proc=subprocess.run(['pdftotext','-f',str(page),'-l',str(page),'-layout',str(path),'-'],capture_output=True,timeout=30,check=True)
                                require(len(proc.stdout)<=2_000_000,'Page extraction too large')
                                cache[key]=proc.stdout.decode('utf-8')
                            chunks.append(cache[key])
                        item['status']='text-match' if normalize(e['quote']) in normalize(' '.join(chunks)) else 'quote-mismatch'
                    except (OSError,ValueError,subprocess.SubprocessError,UnicodeError):item['status']='extraction-unavailable'
                reports.append(item)
    return {'scope':'hash and normalized transcription/location only; no semantic verification','evidence':reports,
            'all_text_matched':bool(reports) and all(r['status']=='text-match' for r in reports)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--source-map',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:
        result=check(load(a.input),json.loads(a.source_map.read_text(encoding='utf-8')))
        with a.report.open('x',encoding='utf-8') as out:out.write(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'all_text_matched':result['all_text_matched'],'semantic_review':'not-performed'}))
        raise SystemExit(0 if result['all_text_matched'] else 1)
    except (OSError,ValueError,KeyError):p.exit(2,'PDF check failed; inspect the local inputs and choose a new report name.\n')
