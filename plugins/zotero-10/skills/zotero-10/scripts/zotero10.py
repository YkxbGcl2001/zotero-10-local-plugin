#!/usr/bin/env python3
"""Zotero 10 local API writes; preserves the upstream read/import CLI.

Uses only Python's standard library. No SQLite edits, JS injection or cloud API.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import mimetypes
import os
import re
import secrets
import sys
import tempfile
import html
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import zotero as legacy

BASE = os.environ.get('ZOTERO_LOCAL_BASE_URL', 'http://127.0.0.1:23119').rstrip('/')
STATE = Path(os.environ.get('ZOTERO10_STATE_DIR', str(Path.home() / '.codex/zotero10')))
KEY_CHARS = '23456789ABCDEFGHIJKLMNPQRSTUVWXYZ'
LEGACY_COMMANDS = {'enable','disable','restart','probe','inventory','collections','tags',
    'groups','search','export-bibtex','sync-bib','citations','children','fulltext',
    'file-url','cite','selected-target','import-bibtex','import-ris'}

class APIError(RuntimeError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def validate_base(base):
    u = urllib.parse.urlsplit(base)
    if (u.scheme != 'http' or u.hostname not in {'127.0.0.1','localhost','::1'}
        or u.username or u.password or u.path not in {'','/'} or u.query or u.fragment):
        raise APIError(None, 'Use a loopback Zotero Desktop URL; this helper is not a cloud client.')
    return base.rstrip('/')

def key(value):
    if not re.fullmatch(r'[23456789A-NP-Z]{8}', value):
        raise APIError(None, 'Invalid Zotero item/collection key.')
    return value

def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def private_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temp = tempfile.mkstemp(prefix='.zotero10-', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)

class Client:
    def __init__(self, base=BASE, state=STATE, library='users/0'):
        self.base = validate_base(base)
        if not re.fullmatch(r'(users|groups)/\d+', library):
            raise APIError(None, 'Library must be users/0, users/<id>, or groups/<id>.')
        self.prefix = '/api/' + library
        self.state = Path(state)
        self.server_id = None
        self.version = None
        self.auth = None

    def transport(self, path, method='GET', payload=None, raw=None, headers=None, timeout=30):
        if not path.startswith('/api/') or '?' in path and re.search(r'[?&]key=',path):
            raise APIError(None, 'Only local API paths; credentials never belong in URLs.')
        hs = {'Zotero-API-Version':'3', **(headers or {})}
        body = raw
        if payload is not None:
            hs.setdefault('Content-Type','application/json')
            body = json.dumps(payload, ensure_ascii=False).encode()
        req = urllib.request.Request(self.base+path, data=body, headers=hs, method=method)
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout) as r:
                data = r.read()
                rh = {k.lower():v for k,v in r.headers.items()}
                if not data: result = None
                else:
                    try: result = json.loads(data)
                    except ValueError: result = data.decode('utf-8', errors='replace')
                return r.status, rh, result
        except urllib.error.HTTPError as e:
            message = e.read().decode('utf-8', errors='replace')[:1500]
            if self.auth and self.auth.get('key'): message = message.replace(self.auth['key'], '[REDACTED]')
            raise APIError(e.code, f'Zotero HTTP {e.code}: {message}') from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise APIError(None, f'Local API connection interrupted ({type(e).__name__}); no write was retried. Read back the target before retrying.') from None

    def connect(self):
        _, h, _ = self.transport('/api/')
        sid = h.get('zotero-server-id')
        # The root may expose the app version only via the X header.
        self.version = h.get('x-zotero-version')
        if not self.version:
            r = legacy.request('/connector/ping', timeout=3)
            self.version = r.headers.get('X-Zotero-Version') or r.headers.get('x-zotero-version')
        self.server_id = sid
        if sid:
            self.auth_path = self.state/'authorizations'/(hashlib.sha256((self.base+'|'+sid).encode()).hexdigest()+'.json')
            if self.auth_path.exists():
                if self.auth_path.is_symlink(): raise APIError(None, 'Authorization file must not be a symlink.')
                if os.name != 'nt' and self.auth_path.stat().st_mode & 0o077:
                    raise APIError(None, 'Authorization file permissions must be private (0600).')
                a = json.loads(self.auth_path.read_text())
                if a.get('serverID') == sid and a.get('base') == self.base: self.auth = a
        return self

    def require_writes(self):
        if self.server_id is None: self.connect()
        major = re.match(r'(\d+)', self.version or '')
        if not major or int(major.group(1)) < 10 or not self.server_id:
            raise APIError(None, 'Official local writes require Zotero 10+ and Zotero-Server-ID. Read/import commands remain available on older clients.')

    def authorize(self, app_name='Codex Zotero 10'):
        self.require_writes()
        _, _, a = self.transport('/api/local/authorize', 'POST', {'appName':app_name},
            headers={'Zotero-Server-ID':self.server_id}, timeout=300)
        if not isinstance(a,dict) or not re.fullmatch(r'[A-Za-z0-9]{32}', a.get('key','')):
            raise APIError(None, 'Zotero did not return a valid local authorization.')
        self.auth = {**a,'serverID':self.server_id,'base':self.base,'appName':app_name}
        private_json(self.auth_path, self.auth)
        return {'authorized':True,'persistent':bool(a.get('remember')),'serverID':self.server_id}

    def forget(self):
        if self.server_id is None: self.connect()
        if getattr(self,'auth_path',None): self.auth_path.unlink(missing_ok=True)
        self.auth = None
        return {'localCredentialRemoved':True,'serverAuthorizationRevoked':False}

    def call(self, path, method='GET', payload=None, raw=None, headers=None):
        if self.server_id is None: self.connect()
        hs = {'Zotero-Server-ID':self.server_id} if self.server_id else {}
        hs.update(headers or {})
        writing = method != 'GET'
        if writing:
            self.require_writes()
            if not self.auth:
                raise APIError(401, 'No local write authorization. Run authorize and approve the official Zotero dialog.')
            hs['Zotero-API-Key'] = self.auth['key']
        try:
            result = self.transport(path, method, payload, raw, hs)
        except APIError as e:
            if writing and (not self.auth.get('remember') or e.status==401): self.forget()
            raise
        if writing and not self.auth.get('remember'): self.forget()
        return result

    def get(self, path): return self.call(path)[2]
    def item(self, k): return self.get(self.prefix+'/items/'+key(k))['data']

    def patch(self, resource, k, changes, expected=None):
        k = key(k)
        if resource not in {'items','collections','searches'}: raise APIError(None,'Unsupported resource.')
        current = self.get(self.prefix+'/'+resource+'/'+k)['data']
        if expected is not None and expected != current['version']:
            raise APIError(412,'The supplied version is stale; reread and review the target.')
        if any(f in changes for f in ['key','version','dateAdded']):
            raise APIError(None,'Pass changes only; key/version/dateAdded cannot be overwritten.')
        if not changes or all(current.get(f)==v for f,v in changes.items()):
            return {'key':k,'changed':False,'data':current}
        self.call(self.prefix+'/'+resource+'/'+k,'PATCH',changes,
            headers={'If-Unmodified-Since-Version':str(current['version'])})
        after = self.get(self.prefix+'/'+resource+'/'+k)['data']
        for f,v in changes.items():
            if after.get(f) != v and not (f=='deleted' and bool(after.get(f))==bool(v)):
                raise APIError(None,'Write returned success but read-back differs: '+f)
        return {'key':k,'changed':True,'data':after}

    def write_many(self, resource, records):
        self.require_writes()
        if resource not in {'items','collections','searches'} or not isinstance(records,list) or not 1<=len(records)<=50:
            raise APIError(None,'Write 1–50 JSON records for items, collections, or searches.')
        out=[]
        for record in records:
            d=dict(record)
            if d.get('key'):
                key(d['key'])
                if 'version' not in d:
                    try: self.get(self.prefix+'/'+resource+'/'+d['key'])
                    except APIError as e:
                        if e.status != 404: raise
                    else: raise APIError(None,'Existing objects require their reviewed version.')
            else: d['key']=''.join(secrets.choice(KEY_CHARS) for _ in range(8))
            out.append(d)
        # Persist request identities BEFORE sending; never blind-retry a timed-out create.
        op_id=secrets.token_hex(16)
        receipt=self.state/'operations'/(op_id+'.json')
        private_json(receipt, {'serverID':self.server_id,'resource':resource,'records':out,'status':'prepared'})
        token=secrets.token_hex(16)
        _,_,answer=self.call(self.prefix+'/'+resource,'POST',out,headers={'Zotero-Write-Token':token})
        private_json(receipt, {'serverID':self.server_id,'resource':resource,'records':out,'response':answer,'status':'responded'})
        if not isinstance(answer,dict) or answer.get('failed'):
            raise APIError(None,'Batch has failed records; successful records may already be saved. Inspect receipt: '+str(receipt))
        successes=answer.get('successful',answer.get('success',{}))
        if len(successes)+len(answer.get('unchanged',{})) != len(out):
            raise APIError(None,'Incomplete batch response. Inspect receipt: '+str(receipt))
        verified=[self.get(self.prefix+'/'+resource+'/'+d['key'])['data'] for d in out]
        return {'data':verified,'receipt':str(receipt)}

    def update_note(self, k, snippet, mode='replace', expected=None):
        current=self.item(k)
        if current['itemType']!='note': raise APIError(None,'Target is not a note.')
        old=current.get('note','')
        if mode in {'append','prepend'} and snippet in old:
            return {'key':k,'changed':False,'data':current}
        if mode=='replace': new=snippet
        elif mode=='append':
            trimmed=old.rstrip()
            new=(trimmed[:-6]+snippet+'</div>') if trimmed.endswith('</div>') else old+snippet
        else: new=snippet+old
        # Use the version from the read used to construct the note, not a later refetch.
        version=current['version'] if expected is None else expected
        return self.patch('items',k,{'note':new},version)

    def attach(self, parent, path, title=None, resume=None):
        path=Path(path).expanduser().resolve(strict=True)
        size=path.stat().st_size
        if size<=0 or size>=4*1024**3: raise APIError(None,'Attachment must be nonempty and below 4 GB.')
        parent=key(parent); d=self.item(parent)
        if d['itemType'] in {'note','attachment'}: raise APIError(None,'Attach to a regular bibliographic parent.')
        sha=digest(path); md5=digest(path,'md5'); mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if mime=='application/pdf':
            with path.open('rb') as f:
                if not f.read(1024).lstrip().startswith(b'%PDF'): raise APIError(None,'The PDF header is invalid.')
        for child in self.get(self.prefix+'/items/'+parent+'/children?format=json'):
            a=child['data']
            if a.get('itemType')=='attachment' and a.get('linkMode') in {'imported_file','imported_url'}:
                try: u=self.get(self.prefix+'/items/'+a['key']+'/file/view/url')
                except APIError as e:
                    if e.status==404: continue
                    raise
                if isinstance(u,str) and urllib.parse.urlsplit(u).scheme=='file':
                    stored=Path(urllib.parse.unquote(urllib.parse.urlsplit(u).path))
                    if stored.is_file() and digest(stored)==sha:
                        return {'attachmentKey':a['key'],'parentItem':parent,'alreadyPresent':True,'sha256':sha,'storagePath':str(stored)}
        self.require_writes()
        if not self.auth or not self.auth.get('remember'):
            raise APIError(401,'File import needs several writes. Run authorize and choose Always Allow before starting; no attachment was created.')
        title=title or path.name
        if resume:
            ak=key(resume); a=self.item(ak)
            if (a.get('parentItem')!=parent or a.get('linkMode')!='imported_file' or a.get('filename')!=path.name):
                raise APIError(None,'Resume attachment does not match the parent and source filename.')
        else:
            a=self.write_many('items',[{'itemType':'attachment','parentItem':parent,'title':title,
                'linkMode':'imported_file','contentType':mime,'filename':path.name,'tags':[]}])['data'][0]
            ak=a['key']
        receipt=self.state/'operations'/('attachment-'+ak+'.json')
        private_json(receipt,{'serverID':self.server_id,'parentItem':parent,'attachmentKey':ak,
            'source':str(path),'sha256':sha,'status':'metadata-saved'})
        etag=a.get('md5')
        conditions={'If-Match':etag} if etag else {'If-None-Match':'*'}
        meta={'md5':md5,'filename':path.name,'filesize':size,'mtime':path.stat().st_mtime_ns//1000000,'contentType':mime}
        try:
            _,_,upload=self.call(self.prefix+'/items/'+ak+'/file','POST',raw=urllib.parse.urlencode(meta).encode(),
                headers={**conditions,'Content-Type':'application/x-www-form-urlencoded'})
            if not upload.get('exists'):
                u=urllib.parse.urlsplit(upload['url']);b=urllib.parse.urlsplit(self.base)
                if (u.scheme!='http' or u.hostname!=b.hostname or u.port!=b.port
                    or not re.fullmatch(r'/api/local/uploads/[A-Za-z0-9]+',u.path) or u.query or u.fragment):
                    raise APIError(None,'Unexpected upload destination; file was not sent.')
                if upload.get('prefix') or upload.get('suffix'): raise APIError(None,'Unexpected local upload framing.')
                if digest(path)!=sha: raise APIError(None,'Source changed during upload preparation.')
                with path.open('rb') as stream:
                    self.transport(u.path,'POST',raw=stream,headers={'Content-Type':upload.get('contentType',mime),'Content-Length':str(size)},timeout=120)
                self.call(self.prefix+'/items/'+ak+'/file','POST',raw=urllib.parse.urlencode({'upload':upload['uploadKey']}).encode(),
                    headers={**conditions,'Content-Type':'application/x-www-form-urlencoded'})
            url=self.get(self.prefix+'/items/'+ak+'/file/view/url')
            if not isinstance(url,str) or urllib.parse.urlsplit(url).scheme!='file': raise APIError(None,'No local stored file URL returned.')
            stored=Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path))
            if not stored.is_file() or digest(stored)!=sha: raise APIError(None,'Stored file SHA-256 differs from source.')
        except APIError as e:
            raise APIError(e.status,str(e)+f' Attachment metadata may exist: {ak}. Keep the source; inspect the receipt {receipt} and resume explicitly.') from None
        result={'attachmentKey':ak,'parentItem':parent,'alreadyPresent':False,'sha256':sha,'storagePath':str(stored),'verified':True}
        private_json(receipt,result)
        return result

    def relate(self, a, b):
        a=key(a);b=key(b)
        if a==b:raise APIError(None,'An item cannot be related to itself.')
        ra=self.get(self.prefix+'/items/'+a);rb=self.get(self.prefix+'/items/'+b)
        def uri(record):
            lib=record['library']
            if not isinstance(lib['id'],int) or lib['id']<=0:raise APIError(None,'A canonical library identity is required for related-item URIs.')
            segment='users' if lib['type']=='user' else 'groups'
            return f"http://zotero.org/{segment}/{lib['id']}/items/{record['key']}"
        records=[]
        for own,other in [(ra,rb),(rb,ra)]:
            rel=dict(own['data'].get('relations',{}));v=rel.get('dc:relation',[])
            v=[v] if isinstance(v,str) else list(v)
            if uri(other) not in v:v.append(uri(other))
            rel['dc:relation']=v
            records.append({'key':own['key'],'version':own['data']['version'],'relations':rel})
        return self.write_many('items',records)

def parser():
    p=argparse.ArgumentParser(description='Zotero 10 official local API. Upstream read/import commands are also accepted.')
    p.add_argument('--library',default='users/0',help='users/0 (default) or groups/<id>')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ['status','auth-status','authorize','forget-authorization']:
        s=sub.add_parser(name);s.add_argument('--json',action='store_true')
        if name=='authorize':s.add_argument('--app-name',default='Codex Zotero 10')
    for name in ['write-items','write-collections','write-searches']:
        s=sub.add_parser(name);s.add_argument('--file',required=True);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('get-item');s.add_argument('key')
    s=sub.add_parser('update-item');s.add_argument('key');s.add_argument('--file',required=True);s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('update-note');s.add_argument('key');s.add_argument('--html',required=True);s.add_argument('--mode',choices=['replace','append','prepend'],default='replace');s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('create-note');s.add_argument('parent');s.add_argument('--html',required=True);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('set-collections');s.add_argument('key');s.add_argument('collections',nargs='*');s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('trash-item');s.add_argument('key');s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('restore-item');s.add_argument('key');s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('reparent-item');s.add_argument('key');s.add_argument('parent');s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('delete-item');s.add_argument('key');s.add_argument('--permanent',action='store_true');s.add_argument('--yes',action='store_true')
    s=sub.add_parser('attach-file');s.add_argument('parent');s.add_argument('file');s.add_argument('--title');s.add_argument('--resume-key');s.add_argument('--yes',action='store_true')
    for name in ['schema','item-types','item-fields','creator-fields','saved-searches']:
        sub.add_parser(name)
    for name in ['type-fields','creator-types']:
        s=sub.add_parser(name);s.add_argument('item_type')
    for name in ['annotations','saved-search-items']:
        s=sub.add_parser(name);s.add_argument('key')
    s=sub.add_parser('query');s.add_argument('--q');s.add_argument('--qmode',choices=['titleCreatorYear','everything'],default='titleCreatorYear');s.add_argument('--item-type');s.add_argument('--tag');s.add_argument('--collection');s.add_argument('--include-trash',action='store_true')
    s.add_argument('--sort',choices=['title','creator','date','dateAdded','dateModified'],default='dateModified');s.add_argument('--direction',choices=['asc','desc'],default='desc')
    s=sub.add_parser('set-tags');s.add_argument('key');s.add_argument('tags',nargs='*');s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('update-collection');s.add_argument('key');s.add_argument('--file',required=True);s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('update-search');s.add_argument('key');s.add_argument('--file',required=True);s.add_argument('--version',type=int);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('write-fulltext');s.add_argument('key');s.add_argument('--file',required=True);s.add_argument('--yes',action='store_true')
    s=sub.add_parser('export-file');s.add_argument('key');s.add_argument('--out',required=True)
    s=sub.add_parser('relate-items');s.add_argument('a');s.add_argument('b');s.add_argument('--yes',action='store_true')
    s=sub.add_parser('export-library');s.add_argument('--format',choices=['bibtex','biblatex','ris','csljson','csv','mods','rdf_zotero'],default='bibtex');s.add_argument('--collection');s.add_argument('--out',required=True)
    sub.add_parser('duplicate-candidates')
    s=sub.add_parser('report');s.add_argument('keys',nargs='+');s.add_argument('--out',required=True)
    return p

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    validate_base(BASE);legacy.DEFAULT_BASE_URL=BASE
    if argv and argv[0] in LEGACY_COMMANDS: return legacy.main(argv)
    args=parser().parse_args(argv);c=Client(library=args.library).connect();cmd=args.command
    if cmd in {'status','auth-status'}:
        result={'zoteroVersion':c.version,'localAPI':True,'serverID':c.server_id,
            'writeSupported':bool(c.server_id and re.match(r'^(1[0-9]|[2-9][0-9])\.',c.version or '')),
            'credentialCached':bool(c.auth),'persistent':bool(c.auth and c.auth.get('remember')),
            'legacyReadCommands':sorted(LEGACY_COMMANDS)}
    elif cmd=='authorize':result=c.authorize(args.app_name)
    elif cmd=='forget-authorization':result=c.forget()
    elif cmd=='get-item':result=c.item(args.key)
    elif cmd in {'schema','item-types','item-fields','creator-fields'}:
        result=c.get('/api/'+{'schema':'schema','item-types':'itemTypes','item-fields':'itemFields','creator-fields':'creatorFields'}[cmd])
    elif cmd in {'type-fields','creator-types'}:
        result=c.get('/api/'+('itemTypeFields' if cmd=='type-fields' else 'itemTypeCreatorTypes')+'?'+urllib.parse.urlencode({'itemType':args.item_type}))
    elif cmd=='saved-searches':result=c.get(c.prefix+'/searches')
    elif cmd=='saved-search-items':result=c.get(c.prefix+'/searches/'+key(args.key)+'/items')
    elif cmd=='annotations':
        parent=c.item(args.key)
        if parent['itemType']!='attachment':raise APIError(None,'Annotations belong to a PDF/EPUB/HTML attachment, not the bibliographic parent.')
        result=[x for x in c.get(c.prefix+'/items/'+key(args.key)+'/children') if x['data']['itemType']=='annotation']
    elif cmd=='query':
        params={'qmode':args.qmode,'sort':args.sort,'direction':args.direction}
        for flag,name in [('q','q'),('item_type','itemType'),('tag','tag')]:
            if getattr(args,flag):params[name]=getattr(args,flag)
        if args.include_trash:params['includeTrashed']='1'
        route=c.prefix+'/items'
        if args.collection:route=c.prefix+'/collections/'+key(args.collection)+'/items'
        result=c.get(route+'?'+urllib.parse.urlencode(params))
    elif cmd=='export-file':
        u=c.get(c.prefix+'/items/'+key(args.key)+'/file/view/url')
        if not isinstance(u,str) or urllib.parse.urlsplit(u).scheme!='file':raise APIError(None,'No stored local file URL.')
        src=Path(urllib.parse.unquote(urllib.parse.urlsplit(u).path));dest=Path(args.out).expanduser()
        if dest.exists():raise APIError(None,'Output already exists; do not overwrite an existing PDF implicitly.')
        import shutil
        shutil.copy2(src,dest)
        if digest(src)!=digest(dest):raise APIError(None,'Exported file verification failed.')
        result={'path':str(dest.resolve()),'sha256':digest(dest)}
    elif cmd=='export-library':
        route=c.prefix+'/items'
        if args.collection:route=c.prefix+'/collections/'+key(args.collection)+'/items'
        result=c.get(route+'?'+urllib.parse.urlencode({'format':args.format,'limit':1000000}))
        dest=Path(args.out)
        if dest.exists():raise APIError(None,'Output already exists; choose a new export filename.')
        dest.write_text(result if isinstance(result,str) else json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        result={'path':str(dest.resolve()),'format':args.format}
    elif cmd=='duplicate-candidates':
        rows=c.get(c.prefix+'/items/top?format=json');groups={}
        for r in rows:
            d=r['data'];doi=d.get('DOI','').strip().lower();doi=re.sub(r'^https?://(?:dx\.)?doi\.org/','',doi)
            ident=('doi:'+doi) if doi else ('title:'+re.sub(r'\W+','',d.get('title','').casefold()))
            if ident in {'title:','doi:'}:continue
            groups.setdefault(ident,[]).append({'key':r['key'],'title':d.get('title'),'date':d.get('date'),'creators':d.get('creators')})
        result={'method':'DOI or normalized-title candidate grouping, not Zotero native duplicate detection','groups':[v for v in groups.values() if len(v)>1],'merged':False}
    elif cmd=='report':
        parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Zotero 文献报告</title><body>']
        for k in args.keys:
            d=c.item(k);parts.append('<article><h2>'+html.escape(d.get('title',''))+'</h2>')
            for f in ['DOI','date','publicationTitle','abstractNote']:
                if d.get(f):parts.append('<p><b>'+f+'</b> '+html.escape(str(d[f]))+'</p>')
            names=[x.get('name') or (x.get('firstName','')+' '+x.get('lastName','')).strip() for x in d.get('creators',[])]
            if names:parts.append('<p><b>作者</b> '+html.escape('; '.join(names))+'</p>')
            for r in c.get(c.prefix+'/items/'+key(k)+'/children'):
                child=r['data']
                if child['itemType']=='note':parts.append('<section>'+child['note']+'</section>')
                elif child['itemType']=='attachment':parts.append('<p><b>附件</b> '+html.escape(child.get('title','')+' / '+child.get('filename','')+' / '+child['key'])+'</p>')
            parts.append('</article>')
        parts.append('</body></html>');dest=Path(args.out)
        if dest.exists():raise APIError(None,'Output already exists; choose a new report filename.')
        dest.write_text('\n'.join(parts),encoding='utf-8');result={'path':str(dest.resolve()),'items':len(args.keys),'kind':'metadata and child-note HTML report'}
    else:
        if not args.yes: raise APIError(None,'Write not confirmed: use --yes only for work already authorized by the user.')
        if cmd.startswith('write-'):result=c.write_many(cmd[6:],json.loads(Path(args.file).read_text()))
        elif cmd=='update-item':result=c.patch('items',args.key,json.loads(Path(args.file).read_text()),args.version)
        elif cmd=='update-note':result=c.update_note(args.key,Path(args.html).read_text(),args.mode,args.version)
        elif cmd=='create-note':
            parent=c.item(args.parent)
            if parent['itemType'] in {'note','attachment'}:raise APIError(None,'Create a child note under a regular item.')
            result=c.write_many('items',[{'itemType':'note','parentItem':key(args.parent),'note':Path(args.html).read_text(),'tags':[]}])
        elif cmd=='set-collections':result=c.patch('items',args.key,{'collections':[key(k) for k in args.collections]},args.version)
        elif cmd=='set-tags':result=c.patch('items',args.key,{'tags':[{'tag':t,'type':0} for t in args.tags]},args.version)
        elif cmd in {'update-collection','update-search'}:
            result=c.patch('collections' if cmd=='update-collection' else 'searches',args.key,json.loads(Path(args.file).read_text()),args.version)
        elif cmd=='write-fulltext':
            body=json.loads(Path(args.file).read_text())
            if not isinstance(body,dict) or not isinstance(body.get('content'),str):raise APIError(None,'Full-text JSON must contain a content string.')
            for f in ['indexedChars','totalChars','indexedPages','totalPages']:
                if f in body and (not isinstance(body[f],int) or isinstance(body[f],bool) or body[f]<0):raise APIError(None,'Full-text counters must be nonnegative integers.')
            c.call(c.prefix+'/items/'+key(args.key)+'/fulltext','PUT',body)
            result=c.get(c.prefix+'/items/'+key(args.key)+'/fulltext')
            if result.get('content')!=body['content']:raise APIError(None,'Full-text read-back mismatch.')
        elif cmd=='relate-items':result=c.relate(args.a,args.b)
        elif cmd=='trash-item':result=c.patch('items',args.key,{'deleted':1},args.version)
        elif cmd=='restore-item':result=c.patch('items',args.key,{'deleted':0},args.version)
        elif cmd=='reparent-item':
            child=c.item(args.key);parent=c.item(args.parent)
            if child['itemType'] not in {'note','attachment','annotation'}:raise APIError(None,'Only notes, attachments and annotations can have a parent.')
            if (child['itemType']=='annotation' and parent['itemType']!='attachment') or (child['itemType']!='annotation' and parent['itemType'] in {'note','attachment','annotation'}):raise APIError(None,'The parent type does not match the child type.')
            result=c.patch('items',args.key,{'parentItem':key(args.parent)},args.version)
        elif cmd=='delete-item':
            if not args.permanent:raise APIError(None,'Use trash-item for recoverable removal; permanent deletion also requires --permanent.')
            d=c.item(args.key);c.call(c.prefix+'/items/'+key(args.key),'DELETE',headers={'If-Unmodified-Since-Version':str(d['version'])});result={'key':args.key,'permanentlyDeleted':True}
        elif cmd=='attach-file':result=c.attach(args.parent,args.file,args.title,args.resume_key)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except APIError as e:
        print(json.dumps({'error':str(e),'status':e.status},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(1)
