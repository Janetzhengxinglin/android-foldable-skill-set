"""Check sibling Android skills and capture dependencies; no App or network actions."""
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REQUIRED={
 'android-foldable-page-capture':['SKILL.md','scripts/capture.py','scripts/image_batches.py','references/image-processing.md','references/handoff.json'],
 'android-foldable-design-guidelines':['SKILL.md','scripts/seed_review.py','scripts/validate_rules.py','scripts/validate_review.py','references/rules.json'],
 'android-foldable-adaptation-review':['SKILL.md','scripts/workflow.py','scripts/build_report.py','references/handoff.json']}

def main():
 errors=[]
 for name,paths in REQUIRED.items():
  for p in paths:
   if not (ROOT/name/p).is_file():errors.append('缺少 '+name+'/'+p)
 for name in ['android-foldable-page-capture','android-foldable-adaptation-review']:
  p=ROOT/name/'references/handoff.json'
  if p.is_file() and json.loads(p.read_text(encoding='utf-8')).get('schema_version')!=1:errors.append('交接版本不兼容: '+name)
 rule_file=ROOT/'android-foldable-design-guidelines/references/rules.json'
 if rule_file.is_file() and json.loads(rule_file.read_text(encoding='utf-8')).get('schema_version')!=1:errors.append('规范数据版本不兼容')
 for name in ['ffmpeg','ffprobe']:
  if not shutil.which(name):errors.append('缺少 '+name)
 if errors:
  print(json.dumps({'ready':False,'errors':errors},ensure_ascii=False));sys.exit(1)
 script=ROOT/'android-foldable-design-guidelines/scripts/validate_rules.py'
 r=subprocess.run([sys.executable,'-B',str(script)],capture_output=True,text=True)
 if r.returncode:print(r.stderr);sys.exit(1)
 print(json.dumps({'ready':True,'skills':list(REQUIRED),'schema_version':1,'rule_check':r.stdout.strip()},ensure_ascii=False))
if __name__=='__main__':main()
