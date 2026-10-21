import unittest,tempfile,json,os,sys,hashlib,shutil,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/zotero-10/scripts'))
from zotero10 import Client,APIError,private_json,validate_base,main,digest
class Fake(Client):
 def __init__(self,state,sid='SERVER1',version='10.0.6'):
  super().__init__('http://127.0.0.1:23119',state);self.sid=sid;self.ver=version;self.calls=[];self.fail=None;self.partial=False
  self.db={'ABCDEFGH':{'key':'ABCDEFGH','version':3,'itemType':'journalArticle','title':'Keep title','collections':['23456789']},'BCDEFGHJ':{'key':'BCDEFGHJ','version':2,'itemType':'note','parentItem':'ABCDEFGH','note':'<div><p>original</p></div>'}}
  self.files={};self.uploaded=None;self.denied=False
 def transport(self,path,method='GET',payload=None,raw=None,headers=None,timeout=30):
  headers=headers or {};self.calls.append((path,method,payload,headers));path=path.split('?',1)[0]
  if path=='/api/':return 200,{'zotero-server-id':self.sid,'x-zotero-version':self.ver},'OK'
  if path=='/api/local/authorize':
   if self.denied:raise APIError(403,'denied')
   return 200,{}, {'key':'A'*32,'remember':True}
  if method!='GET' and not path.startswith('/api/local/uploads/'):
   assert headers.get('Zotero-Server-ID')==self.sid
   assert headers.get('Zotero-API-Key')=='A'*32
  if self.fail and method!='GET':raise self.fail
  if path.endswith('/children'):
   par=path.split('/')[-2];return 200,{},[{'data':d} for d in self.db.values() if d.get('parentItem')==par]
  if path.endswith('/file/view/url'):
   k=path.split('/')[-4]
   if k not in self.files:raise APIError(404,'missing file')
   return 200,{},Path(self.files[k]).as_uri()
  if path.endswith('/file'):
   k=path.split('/')[-2];params=urllib.parse.parse_qs(raw.decode())
   if 'upload' not in params:return 200,{}, {'url':self.base+'/api/local/uploads/ABC123','uploadKey':'ABC123','contentType':'application/pdf','prefix':'','suffix':''}
   f=Path(self.state)/('stored-'+k+'.pdf');f.write_bytes(self.uploaded);self.files[k]=str(f);self.db[k]['md5']=digest(f,'md5');return 204,{},None
  if path.startswith('/api/local/uploads/'):
   self.uploaded=raw.read() if hasattr(raw,'read') else raw;return 201,{},None
  parts=path.split('?')[0].split('/');k=parts[-1]
  if method=='GET':
   if k not in self.db:raise APIError(404,'not found')
   return 200,{}, {'data':dict(self.db[k])}
  if method=='PATCH':
   if headers.get('If-Unmodified-Since-Version')!=str(self.db[k]['version']):raise APIError(412,'stale')
   self.db[k].update(payload);self.db[k]['version']+=1;return 204,{},None
  if method=='POST':
   success={};failed={}
   for i,d in enumerate(payload):
    if self.partial and i==1:failed[str(i)]={'code':400};continue
    self.db[d['key']]={**self.db.get(d['key'],{}),**d,'version':1};success[str(i)]={'key':d['key']}
   return 200,{}, {'successful':success,'failed':failed,'unchanged':{}}
  raise AssertionError((path,method))
class Test(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.c=Fake(Path(self.t.name)).connect()
 def tearDown(self):self.t.cleanup()
 def auth(self,persistent=True):
  self.c.authorize();self.c.auth['remember']=persistent;private_json(self.c.auth_path,self.c.auth)
 def test_loopback_only(self):
  for b in ['https://api.zotero.org','http://127.0.0.1@evil.org','http://localhost:23119/path','http://localhost:23119?key=secret']:
   with self.assertRaises(APIError):validate_base(b)
 def test_no_key_no_write(self):
  with self.assertRaises(APIError):self.c.patch('items','ABCDEFGH',{'title':'new'})
  self.assertFalse(any(m=='PATCH' for _,m,_,_ in self.c.calls))
 def test_versioned_partial_update(self):
  self.auth();self.c.patch('items','ABCDEFGH',{'title':'new'},3)
  self.assertEqual(self.c.db['ABCDEFGH']['collections'],['23456789'])
  self.assertEqual(self.c.calls[-2][3]['If-Unmodified-Since-Version'],'3')
 def test_reviewed_stale_version_stops(self):
  self.auth()
  with self.assertRaises(APIError) as cm:self.c.patch('items','ABCDEFGH',{'title':'new'},2)
  self.assertEqual(cm.exception.status,412);self.assertFalse(any(m=='PATCH' for _,m,_,_ in self.c.calls))
 def test_server_412_no_retry(self):
  self.auth();self.c.fail=APIError(412,'conflict')
  with self.assertRaises(APIError):self.c.patch('items','ABCDEFGH',{'title':'new'})
  self.assertEqual(sum(m=='PATCH' for _,m,_,_ in self.c.calls),1)
 def test_note_append_preserves_wrapper_parent_id(self):
  self.auth();self.c.update_note('BCDEFGHJ','<p>addition</p>','append')
  self.assertEqual(self.c.db['BCDEFGHJ']['note'],'<div><p>original</p><p>addition</p></div>')
  self.assertEqual(self.c.db['BCDEFGHJ']['parentItem'],'ABCDEFGH')
  n=len(self.c.calls);self.c.update_note('BCDEFGHJ','<p>addition</p>','append')
  self.assertFalse(any(m=='PATCH' for _,m,_,_ in self.c.calls[n:]))
 def test_existing_note_read_race(self):
  self.auth();orig=self.c.item
  def raced(k):
   d=orig(k);self.c.db[k]['version']+=1;return d
  self.c.item=raced
  with self.assertRaises(APIError):self.c.update_note('BCDEFGHJ','<p>new</p>')
  self.assertIn('original',self.c.db['BCDEFGHJ']['note'])
 def test_new_child_note_generated_key(self):
  self.auth();r=self.c.write_many('items',[{'itemType':'note','parentItem':'ABCDEFGH','note':'<p>new</p>','tags':[]}])
  self.assertEqual(r['data'][0]['parentItem'],'ABCDEFGH');self.assertTrue(Path(r['receipt']).is_file())
 def test_create_with_explicit_new_keys(self):
  self.auth();r=self.c.write_many('items',[{'key':'CDEFGHJK','itemType':'note','parentItem':'ABCDEFGH','note':'<p>new</p>'}]);self.assertEqual(r['data'][0]['key'],'CDEFGHJK')
 def test_existing_requires_reviewed_version(self):
  self.auth()
  with self.assertRaises(APIError):self.c.write_many('items',[{'key':'ABCDEFGH','title':'new'}])
 def test_partial_batch_reports_failure(self):
  self.auth();self.c.partial=True
  with self.assertRaises(APIError):self.c.write_many('items',[{'itemType':'book','title':'one'},{'itemType':'book','title':'two'}])
  self.assertEqual(sum(m=='POST' and path.endswith('/items') for path,m,_,_ in self.c.calls),1)
 def test_single_use_consumed_even_on_conflict(self):
  self.auth(False);self.c.fail=APIError(412,'conflict')
  with self.assertRaises(APIError):self.c.patch('items','ABCDEFGH',{'title':'new'})
  self.assertIsNone(self.c.auth);self.assertFalse(self.c.auth_path.exists())
 def test_credential_is_private_and_server_bound(self):
  self.auth();self.assertEqual(self.c.auth_path.stat().st_mode&0o777,0o600)
  other=Fake(self.c.state,sid='SERVER2').connect();self.assertIsNone(other.auth)
 def test_401_clears_stale_key(self):
  self.auth();self.c.fail=APIError(401,'invalid')
  with self.assertRaises(APIError):self.c.patch('items','ABCDEFGH',{'title':'new'})
  self.assertIsNone(self.c.auth)
 def test_denied_does_not_cache_key(self):
  self.c.denied=True
  with self.assertRaises(APIError):self.c.authorize()
  self.assertFalse(self.c.auth_path.exists())
 def test_multistep_without_persistent_key_creates_nothing(self):
  f=Path(self.t.name)/'source.pdf';f.write_bytes(b'%PDF-1.7\ncontent');self.auth(False)
  with self.assertRaises(APIError):self.c.attach('ABCDEFGH',f)
  self.assertFalse(any(path.endswith('/items') and m=='POST' for path,m,_,_ in self.c.calls))
 def test_attachment_upload_hash_and_dedup(self):
  self.auth();f=Path(self.t.name)/'source.pdf';f.write_bytes(b'%PDF-1.7\nrealbytes');r=self.c.attach('ABCDEFGH',f)
  self.assertTrue(r['verified']);self.assertEqual(digest(r['storagePath']),digest(f));count=len(self.c.db)
  r2=self.c.attach('ABCDEFGH',f);self.assertTrue(r2['alreadyPresent']);self.assertEqual(len(self.c.db),count)
 def test_attachment_rejects_remote_upload_url(self):
  self.auth();f=Path(self.t.name)/'source.pdf';f.write_bytes(b'%PDF-1.7\nrealbytes');original=self.c.transport
  def altered(path,*args,**kwargs):
   r=original(path,*args,**kwargs)
   if path.endswith('/file') and r[2] and 'url' in r[2]:r[2]['url']='https://evil.example/upload'
   return r
  self.c.transport=altered
  with self.assertRaises(APIError):self.c.attach('ABCDEFGH',f)
  self.assertIsNone(self.c.uploaded)
 def test_invalid_note_target(self):
  self.auth()
  with self.assertRaises(APIError):self.c.update_note('ABCDEFGH','bad')
 def test_old_client_write_refused(self):
  c=Fake(self.c.state,version='9.0.3').connect()
  with self.assertRaises(APIError):c.authorize()
if __name__=='__main__':unittest.main(verbosity=2)
