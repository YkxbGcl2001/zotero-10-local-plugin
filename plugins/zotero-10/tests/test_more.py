import sys,unittest,io,json,tempfile,contextlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_zotero10 import Fake
import zotero10
class Extra(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.c=Fake(Path(self.t.name)).connect();self.c.authorize()
 def tearDown(self):self.t.cleanup()
 def run_cli(self,args):
  buf=io.StringIO()
  with patch('zotero10.Client',return_value=self.c),contextlib.redirect_stdout(buf):zotero10.main(args)
  return json.loads(buf.getvalue())
 def test_cli_does_not_write_without_yes(self):
  f=Path(self.t.name)/'note.html';f.write_text('<p>new</p>')
  with self.assertRaises(zotero10.APIError):self.run_cli(['update-note','BCDEFGHJ','--html',str(f)])
  self.assertFalse(any(m=='PATCH' for _,m,_,_ in self.c.calls))
 def test_set_tags_preserves_metadata(self):
  r=self.run_cli(['set-tags','ABCDEFGH','材料','待读','--yes']);self.assertEqual(r['data']['tags'],[{'tag':'材料','type':0},{'tag':'待读','type':0}]);self.assertEqual(r['data']['title'],'Keep title')
 def test_set_collections_is_complete_list(self):
  r=self.run_cli(['set-collections','ABCDEFGH','CDEFGHJK','--yes']);self.assertEqual(r['data']['collections'],['CDEFGHJK'])
 def test_trash_and_restore(self):
  self.run_cli(['trash-item','ABCDEFGH','--yes']);self.assertEqual(self.c.db['ABCDEFGH']['deleted'],1)
  self.run_cli(['restore-item','ABCDEFGH','--yes']);self.assertEqual(self.c.db['ABCDEFGH']['deleted'],0)
 def test_note_reparent_preserves_content(self):
  self.c.db['CDEFGHJK']={'key':'CDEFGHJK','version':1,'itemType':'book','title':'second'}
  self.run_cli(['reparent-item','BCDEFGHJ','CDEFGHJK','--yes']);self.assertEqual(self.c.db['BCDEFGHJ']['parentItem'],'CDEFGHJK');self.assertIn('original',self.c.db['BCDEFGHJ']['note'])
 def test_reparent_regular_item_refused(self):
  with self.assertRaises(zotero10.APIError):self.run_cli(['reparent-item','ABCDEFGH','BCDEFGHJ','--yes'])
 def test_report_is_read_only_and_includes_notes(self):
  f=Path(self.t.name)/'report.html';r=self.run_cli(['report','ABCDEFGH','--out',str(f)]);self.assertIn('original',f.read_text());self.assertEqual(r['items'],1);self.assertFalse(any(m=='PATCH' for _,m,_,_ in self.c.calls))
 def test_export_does_not_overwrite(self):
  f=Path(self.t.name)/'already.pdf';f.write_bytes(b'KEEP')
  self.c.db['CDEFGHJK']={'key':'CDEFGHJK','version':1,'itemType':'attachment'};src=Path(self.t.name)/'source.pdf';src.write_bytes(b'%PDF-1.7');self.c.files['CDEFGHJK']=str(src)
  with self.assertRaises(zotero10.APIError):self.run_cli(['export-file','CDEFGHJK','--out',str(f)])
  self.assertEqual(f.read_bytes(),b'KEEP')
 def test_legacy_commands_still_routed(self):
  with patch('zotero10.legacy.main',return_value=0) as m:zotero10.main(['export-bibtex','--item-key','ABCDEFGH']);m.assert_called_once_with(['export-bibtex','--item-key','ABCDEFGH'])
 def test_library_argument_validation(self):
  with self.assertRaises(zotero10.APIError):zotero10.Client(library='groups/../items')
if __name__=='__main__':unittest.main(verbosity=2)
