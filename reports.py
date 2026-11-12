"""Review drone heatmap runs and export a self-contained HTML evidence report."""
import argparse
import base64
import hashlib
import html
import io
import json
import math
from pathlib import Path
import uuid
from datetime import datetime,timezone
import numpy as np
from PIL import Image,ImageDraw

DECISIONS=('confirmed','false_alert','needs_review')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def asset(root,relative):
    path=(Path(root)/relative).resolve()
    if not path.is_relative_to(Path(root).resolve()): raise ValueError('Asset escapes the run directory')
    if not path.is_file(): raise ValueError(f'Missing asset: {relative}')
    return path


def load_run(root):
    root=Path(root).resolve(); metadata=json.loads((root/'run.json').read_text(encoding='utf-8'))
    rows=[]; seen=set()
    for line in (root/'frames.jsonl').read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        row=json.loads(line)
        if type(row.get('frame')) is not int or row['frame']<0 or row['frame'] in seen:
            raise ValueError('Frame IDs must be unique nonnegative integers')
        if not isinstance(row.get('timestamp_s'),(int,float)) or not math.isfinite(row['timestamp_s']) or row['timestamp_s']<0:
            raise ValueError('Invalid frame timestamp')
        seen.add(row['frame']); rows.append(row)
    if not rows: raise ValueError('No frame records')
    return root,metadata,rows


def heatmap(root,row):
    path=asset(root,row['heatmap'])
    offset=row.get('heatmap_offset_bytes')
    if offset is None:
        grid=np.load(path,allow_pickle=False)
    else:
        if type(offset) is not int or offset<0 or offset%4096: raise ValueError('Invalid packed heatmap offset')
        with path.open('rb') as source:
            source.seek(offset); payload=source.read(4096)
        if len(payload)!=4096: raise ValueError('Truncated packed heatmap')
        grid=np.frombuffer(payload,dtype=np.uint8).reshape(64,64)
    if grid.shape!=(64,64) or grid.dtype!=np.uint8: raise ValueError('Expected a uint8 64x64 heatmap')
    return grid


def binding(root,row):
    """A changed run, manifest or evidence invalidates an earlier review."""
    identity={'run':digest(Path(root)/'run.json'),'manifest':digest(Path(root)/'frames.jsonl'),
              'frame':row['frame'],'grid':hashlib.sha256(heatmap(root,row).tobytes()).hexdigest(),
              'evidence':[(path,digest(asset(root,path))) for path in row.get('evidence',[])]}
    return hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()


def save_review(root,row,decision,reviewer,notes='',directory=None):
    if decision not in DECISIONS or not reviewer.strip(): raise ValueError('Choose a decision and enter a reviewer name')
    directory=Path(directory) if directory else Path(root)/'reviews'
    directory.mkdir(parents=True,exist_ok=True)
    record={'schema_version':1,'frame':row['frame'],'binding':binding(root,row),
            'decision':decision,'reviewer':reviewer.strip(),'notes':notes,
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'review_id':uuid.uuid4().hex}
    path=directory/(record['review_id']+'.json')
    with path.open('x',encoding='utf-8') as stream: json.dump(record,stream,indent=2)
    return path


def reviews_for(root,row,directory=None):
    directory=Path(directory) if directory else Path(root)/'reviews'
    current=binding(root,row); valid=[]; stale=[]
    for path in sorted(directory.glob('*.json')):
        record=json.loads(path.read_text(encoding='utf-8'))
        if record.get('frame')==row['frame']:
            if record.get('binding')==current and record.get('decision') in DECISIONS: valid.append(record)
            else: stale.append(record)
    return valid,stale


def grid_image(grid):
    red=grid; blue=255-grid; green=np.minimum(grid,255-grid)
    return Image.fromarray(np.stack([red,green,blue],axis=-1)).resize((320,320),Image.Resampling.NEAREST)


def embedded(image):
    image=image.convert('RGB'); image.thumbnail((1280,1280))
    stream=io.BytesIO(); image.save(stream,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(stream.getvalue()).decode()


def export_html(root,output,directory=None):
    root,metadata,rows=load_run(root); output=Path(output)
    if output.exists(): raise ValueError('Choose a new report path')
    esc=lambda value:html.escape(str(value),quote=True)
    sections=[]
    for row in rows:
        if not row.get('suspicious'): continue
        reviews,stale=reviews_for(root,row,directory)
        pictures=[f'<img alt="Defect-score heatmap" src="{embedded(grid_image(heatmap(root,row)))}">']
        for relative in row.get('evidence',[]):
            with Image.open(asset(root,relative)) as image: url=embedded(image)
            pictures.append(f'<figure><img alt="Source evidence" src="{url}"><figcaption>{esc(relative)}</figcaption></figure>')
        annotations=''.join(f"<li>{esc(r['decision'])} — {esc(r['reviewer'])} ({esc(r.get('created_utc',''))}): {esc(r.get('notes',''))}</li>" for r in reviews)
        sections.append(f"<section><h2>Frame {row['frame']} · {row['timestamp_s']:.3f}s</h2>"
            f"<p>Score: {esc(row.get('max_score'))}. Reviews: {len(reviews)} valid, {len(stale)} stale.</p>"
            f"<div class='images'>{''.join(pictures)}</div><ul>{annotations or '<li>Not reviewed</li>'}</ul></section>")
    text=f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>Inspection evidence report</title>
<style>body{{font:16px system-ui;max-width:1200px;margin:40px auto;padding:20px;color:#183047}}section{{border-top:1px solid #bbb;padding:20px 0}}.images{{display:flex;gap:16px;flex-wrap:wrap}}img{{max-width:100%;max-height:420px;object-fit:contain}}figure{{margin:0;max-width:600px}}figcaption{{font-size:12px}}code{{overflow-wrap:anywhere}}</style>
<h1>Inspection evidence report</h1><p>Run status: {esc(metadata.get('status','legacy / unknown'))}.
Synthetic input: {esc(metadata.get('synthetic','unknown'))}. {len(rows)} processed frame records.</p>
<p>Scores describe model output, not structural severity. Review decisions are human assessments.
Multiple reviews are shown together; conflicting decisions are not silently resolved.</p>
<p>Run metadata SHA-256: <code>{digest(root/'run.json')}</code><br>
Frame manifest SHA-256: <code>{digest(root/'frames.jsonl')}</code></p>
<details><summary>Model provenance</summary><pre>{esc(json.dumps(metadata.get('model'),indent=2))}</pre></details>
{''.join(sections) or '<p>No suspicious frames.</p>'}</html>"""
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream: stream.write(text)
    return output


def make_demo(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    (root/'heatmaps').mkdir(); (root/'evidence').mkdir()
    (root/'run.json').write_text(json.dumps({'schema_version':2,'status':'completed','synthetic':True,
        'model':{'backend':'simulated example; no learned defect model'}},indent=2),encoding='utf-8')
    rows=[]
    for i in range(3):
        grid=np.zeros((64,64),np.uint8)
        image=Image.new('RGB',(640,400),(150,150,150)); draw=ImageDraw.Draw(image)
        if i:
            draw.line([(250,100),(290,160),(270,260)],fill='black',width=5)
            grid[16:44,25:31]=220
        relative=f'heatmaps/{i}.npy'; np.save(root/relative,grid,allow_pickle=False)
        evidence=[]
        if i:
            path=f'evidence/{i}.png'; image.save(root/path); evidence.append(path)
        rows.append(dict(frame=i,timestamp_s=float(i),max_score=float(grid.max()/255),suspicious=bool(i),
                         heatmap=relative,evidence=evidence))
    (root/'frames.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    demo=sub.add_parser('demo'); demo.add_argument('--output',type=Path,required=True)
    export=sub.add_parser('export'); export.add_argument('run',type=Path); export.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.command=='demo': make_demo(args.output)
    else: print(export_html(args.run,args.output))


if __name__=='__main__': main()
