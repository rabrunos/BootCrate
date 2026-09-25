"""Explicit, pre-materialization three-way update of approved managed files.

The manifest is local/ignored and removed with bootstrap. This is not a background
updater for projects after materialization.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

MANIFEST = Path('.local/bootcrate-managed.json')


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve(root: Path, relative: str) -> Path:
    if not relative or '\\' in relative:
        raise ValueError('Invalid managed path')
    p = Path(relative)
    if p.is_absolute() or any(x in {'..','.git','.local'} for x in p.parts) or p == Path('.'):
        raise ValueError('Unsafe managed path')
    current = root.resolve()
    for part in p.parts:
        current = current/part
        if current.is_symlink(): raise ValueError('Symlink in managed path: '+relative)
    if not current.resolve().is_relative_to(root.resolve()): raise ValueError('Managed path escapes root')
    return current


def content(root: Path, relative: str) -> bytes | None:
    path = resolve(root,relative)
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size > 2*1024*1024:
        raise ValueError('Unsupported managed file: '+relative)
    return path.read_bytes()


def bootstrap(root: Path) -> None:
    if not (root/'docs/.human/bootstrap').is_dir():
        raise ValueError('Bootstrap has been pruned: do not recreate a manifest for the product')


def create(root: Path, revision: str, paths: list[str]) -> dict:
    bootstrap(root)
    if (root/MANIFEST).exists():raise ValueError('Manifest already exists')
    if not paths or len(paths)!=len(set(paths)):raise ValueError('Supply distinct explicitly approved paths')
    files={}
    for path in paths:
        data=content(root,path)
        if data is None:raise ValueError('Managed source missing: '+path)
        files[path]=hash_bytes(data)
    manifest={'schema':'bootcrate-managed/v1','source_revision':revision,'files':files}
    (root/MANIFEST).parent.mkdir(parents=True,exist_ok=True)
    (root/MANIFEST).write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def read(root: Path) -> dict:
    bootstrap(root)
    raw=(root/MANIFEST).read_text()
    manifest=json.loads(raw)
    if (manifest.get('schema')!='bootcrate-managed/v1' or not isinstance(manifest.get('files'),dict)
        or not manifest.get('source_revision')):raise ValueError('Unsupported or invalid manifest')
    for name,value in manifest['files'].items():
        resolve(root,name)
        if not isinstance(value,str) or len(value)!=64 or any(x not in '0123456789abcdef' for x in value):
            raise ValueError('Invalid base digest')
    return manifest


def preview(root: Path, source: Path, manifest: dict, new_paths: list[str] = ()) -> dict:
    bootstrap(root)
    if len(new_paths)!=len(set(new_paths)):raise ValueError('Duplicate new path')
    actions=[]
    for name in sorted(set(manifest['files'])|set(new_paths)):
        current=content(root,name);next_data=content(source,name)
        base=manifest['files'].get(name)
        c=hash_bytes(current) if current is not None else None
        n=hash_bytes(next_data) if next_data is not None else None
        if base is None:action='add' if c is None and n else 'conflict'
        elif c is None:action='conflict' # deletion may be intentional
        elif c==n:action='unchanged'
        elif c==base:action='remove' if n is None else 'update'
        elif n==base:action='preserve'
        else:action='conflict'
        actions.append({'path':name,'action':action,'current':c,'new':n})
    plan={'schema':'bootcrate-upgrade-plan/v1','base_revision':manifest['source_revision'],'actions':actions}
    plan['digest']=hash_bytes(json.dumps(plan,sort_keys=True,separators=(',',':')).encode())
    return plan


def apply(root: Path, source: Path, expected_digest: str, new_revision: str, new_paths: list[str] = ()) -> dict:
    manifest=read(root)
    plan=preview(root,source,manifest,new_paths)
    if plan['digest']!=expected_digest:raise ValueError('Plan or file contents changed since review')
    if any(x['action']=='conflict' for x in plan['actions']):raise ValueError('Resolve all conflicts explicitly before applying')
    changes=[x for x in plan['actions'] if x['action'] in {'add','remove','update'}]
    before={x['path']:content(root,x['path']) for x in changes}
    written={}
    with tempfile.TemporaryDirectory(prefix='upgrade-',dir=(root/MANIFEST).parent) as td:
        backup=Path(td)
        for i,item in enumerate(changes):
            if before[item['path']] is not None:(backup/str(i)).write_bytes(before[item['path']])
        try:
            if preview(root,source,manifest,new_paths)['digest']!=expected_digest:
                raise ValueError('Files changed during update preparation')
            for item in changes:
                name=item['path'];target=resolve(root,name)
                data=content(source,name)
                if item['action']=='remove':target.unlink();written[name]=None
                else:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    temp=backup/('new-'+str(len(written)))
                    temp.write_bytes(data)
                    os.replace(temp,target);written[name]=hash_bytes(data)
            for item in plan['actions']:
                if item['action']=='remove':manifest['files'].pop(item['path'],None)
                elif item['action'] in {'update','add','unchanged'}:
                    manifest['files'][item['path']]=item['new']
            manifest['source_revision']=new_revision
            target=root/MANIFEST;staged=backup/'manifest-new'
            staged.write_text(json.dumps(manifest,indent=2)+'\n')
            os.replace(staged,target)
        except Exception:
            # Never overwrite another process's edits while recovering our own operation.
            for name,after in written.items():
                if (hash_bytes(content(root,name)) if content(root,name) is not None else None)!=after:
                    raise RuntimeError('Concurrent edit during recovery; manual reconciliation required')
                target=resolve(root,name);old=before[name]
                if old is None:target.unlink(missing_ok=True)
                else:
                    temp=backup/('restore-'+hash_bytes(name.encode()))
                    temp.write_bytes(old);os.replace(temp,target)
            raise
    return {'status':'applied','paths':[x['path'] for x in changes],'revision':new_revision}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest='command',required=True)
    init=subs.add_parser('init');init.add_argument('root',type=Path);init.add_argument('--revision',required=True)
    init.add_argument('paths',nargs='+')
    for command in ('preview','apply'):
        sub=subs.add_parser(command);sub.add_argument('root',type=Path);sub.add_argument('source',type=Path)
        sub.add_argument('--new-path',action='append',default=[])
        if command=='apply':sub.add_argument('--approved-plan-digest',required=True);sub.add_argument('--revision',required=True)
    args=p.parse_args()
    try:
        if args.command=='init':result=create(args.root,args.revision,args.paths)
        elif args.command=='preview':result=preview(args.root,args.source,read(args.root),args.new_path)
        else:result=apply(args.root,args.source,args.approved_plan_digest,args.revision,args.new_path)
        print(json.dumps(result,indent=2));return 0
    except (ValueError,OSError,TypeError,KeyError,RuntimeError) as e:
        print('BLOCKED: '+str(e),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
