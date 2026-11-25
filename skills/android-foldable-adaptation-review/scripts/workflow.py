"""Merge complete captures and hand them to Android rule review without judging pages."""
import argparse,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RULES=ROOT/'android-foldable-design-guidelines'
sys.path.insert(0,str(RULES/'scripts'))
from common import load_input,require,sha,write,read

def merge(captures,run_dir):
 run=Path(run_dir).resolve();run.mkdir(parents=True,exist_ok=True)
 dest=run/'capture.json';require(not dest.exists(),'capture.json 已存在，保留旧轮次并新建目录')
 merged={'schema_version':1,'contexts':[],'pages':[],'evidence':[],'facts':{},'capture_sources':[]}
 for i,p in enumerate(captures):
  p=Path(p).resolve();data=read(p)
  require(data.get('capture_review',{}).get('all_candidates_classified') is True and data['capture_review'].get('all_intervals_reviewed') is True,'原始采集未完成全量回查: '+str(p))
  load_input(p)
  prefix='recording-%02d-'%i
  def new(id):return prefix+id
  def facts(values):return {k:{**v,'evidence_ids':[new(x) for x in v.get('evidence_ids',[])]} for k,v in values.items()}
  for c in data['contexts']:merged['contexts'].append({**c,'id':new(c['id']),'facts':facts(c.get('facts',{}))})
  for e in data['evidence']:
   f=Path(e['path'])
   if not f.is_absolute():f=p.parent/f
   merged['evidence'].append({**e,'id':new(e['id']),'path':os.path.relpath(f.resolve(),run),
                             'page_ids':[new(x) for x in e['page_ids']],'context_ids':[new(x) for x in e['context_ids']]})
  for page in data['pages']:
   merged['pages'].append({**page,'id':new(page['id']),'context_id':new(page['context_id']),
                          'image_evidence_id':new(page['image_evidence_id']),
                          'facts':facts({**data.get('facts',{}),**page.get('facts',{})}),
                          'components':[{**c,'id':new(c['id']),'facts':facts(c.get('facts',{}))} for c in page.get('components',[])]})
  merged['capture_sources'].append({'path':os.path.relpath(p,run),'sha256':sha(p)})
 merged['capture_review']={'all_candidates_classified':True,'all_intervals_reviewed':True,'notes':'各原始录屏已确认完整采集后合并；仍需逐图核对最终清单'}
 write(dest,merged);load_input(dest)
 print('合并',len(captures),'份完整录屏采集，',len(merged['pages']),'个页面状态；未判断规范。')

def prepare(run_dir):
 run=Path(run_dir).resolve();source=run/'capture.json';out=run/'review-input.json'
 require(not out.exists(),'review-input.json 已存在，不覆盖组件库存或既有审查')
 load_input(source);data=copy.deepcopy(read(source))
 data['original_capture']={'path':'capture.json','sha256':sha(source)}
 write(out,data)
 print('已建立工作副本；先逐页补齐组件与事实，再执行 seed。')

def seed(run_dir, profile='screenshot-only'):
 run=Path(run_dir).resolve()
 load_input(run/'review-input.json')
 r=subprocess.run([sys.executable,'-B',str(RULES/'scripts/seed_review.py'),str(run/'review-input.json'),str(run/'review.json'),'--profile',profile])
 require(r.returncode==0,'生成审查记录失败')

def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
 a=s.add_parser('merge');a.add_argument('run_dir');a.add_argument('captures',nargs='+')
 for name in ['prepare','seed']:
  a=s.add_parser(name);a.add_argument('run_dir')
  if name=='seed':a.add_argument('--profile',choices=['screenshot-only','submitted-evidence'],default='screenshot-only')
 args=p.parse_args()
 try:
  if args.command=='merge':merge(args.captures,args.run_dir)
  elif args.command=='prepare':prepare(args.run_dir)
  else:seed(args.run_dir,args.profile)
 except (ValueError,KeyError,TypeError,OSError) as e:p.error(str(e))
if __name__=='__main__':main()
