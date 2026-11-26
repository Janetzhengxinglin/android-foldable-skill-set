import importlib.util,sys,unittest,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'skills/android-foldable-design-guidelines/scripts';sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('validator',root/'validate_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CompletionTests(unittest.TestCase):
 def setUp(self):self.r={'review_strategy':'batch','scope':{'profile':'screenshot-only'},'visual_review':{'page_ids_reviewed':['P1','P2'],'notes':'Clear whole-page sheet with original detail review'},'self_review':{'finding_ids_rechecked':['F1'],'notes':'Confirmed source and report annotation'}}
 def test_batch_without_double_read(self):self.assertEqual(m.validate_completion(self.r,['P1','P2'],['F1']),'batch')
 def test_missing_page(self):
  self.r['visual_review']['page_ids_reviewed']=['P1']
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_duplicate_page(self):
  self.r['visual_review']['page_ids_reviewed']=['P1','P2','P2']
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_clear_findings_need_no_second_image_read(self):
  self.r['self_review']['finding_ids_rechecked']=[]
  self.r['self_review']['notes']='First clear observation and applicable basis suffice; mappings reconciled'
  self.assertEqual(m.validate_completion(self.r,['P1','P2'],['F1']),'batch')
 def test_only_actual_rechecks_are_recorded(self):
  self.assertEqual(m.validate_completion(self.r,['P1','P2'],['F1','F2']),'batch')
 def test_unknown_rechecked_finding(self):
  self.r['self_review']['finding_ids_rechecked']=['F9']
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_duplicate_rechecked_finding(self):
  self.r['self_review']['finding_ids_rechecked']=['F1','F1']
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_missing_completion_notes(self):
  self.r['self_review']['finding_ids_rechecked']=[]
  self.r['self_review']['notes']=''
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_no_findings_still_requires_coverage(self):
  self.r['self_review']['finding_ids_rechecked']=[];self.assertEqual(m.validate_completion(self.r,['P1','P2'],[]),'batch')
 def test_new_unreviewed_seed(self):
  self.r['visual_review']={'page_ids_reviewed':[],'notes':''}
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_batch_not_for_extended_tests(self):
  self.r['scope']['profile']='submitted-evidence'
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
 def test_old_review_still_requires_two_pass(self):
  self.r.pop('review_strategy')
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
  self.r['self_review']={'all_pages_rechecked':True,'all_components_rechecked':True,'notes':'Actual second full review'}
  self.assertEqual(m.validate_completion(self.r,['P1','P2'],['F1']),'two-pass')
 def test_two_pass_needs_components_too(self):
  self.r['review_strategy']='two-pass'
  self.r['self_review']={'all_pages_rechecked':True,'all_components_rechecked':False,'notes':'Only pages'}
  with self.assertRaises(ValueError):m.validate_completion(self.r,['P1','P2'],['F1'])
if __name__=='__main__':unittest.main()
